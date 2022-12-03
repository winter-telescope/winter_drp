"""
Main executable for winterdrp. You can execute the code from the terminal like:

.. codeblock:: bash
    python -m winterdrp -args...
"""
import argparse
import logging
import sys

from astropy import units as u
from astropy.time import Time

from winterdrp.data import Dataset, ImageBatch, clean_cache
from winterdrp.monitor.base_monitor import Monitor
from winterdrp.paths import package_name, raw_img_sub_dir
from winterdrp.pipelines import Pipeline, get_pipeline
from winterdrp.processors.utils import ImageLoader

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description=f"{package_name}: An automated image reduction pipeline, "
    f"developed for WINTER"
)

ln = Time.now() - 1.0 * u.day
parser.add_argument(
    "-n", "--night", default=None, help="Sub-directory to use in the data directory"
)
parser.add_argument("-p", "--pipeline", default="summer", help="Pipeline to be used")
parser.add_argument(
    "-c", "--config", default=None, help="Pipeline configuration to be used"
)
parser.add_argument(
    "-pc", "--postprocessconfig", default=None, help="Pipeline configuration to be used"
)
parser.add_argument(
    "--logfile",
    default=None,
    help="If a path is passed, all logs will be written to this file.",
)
parser.add_argument("--level", default="DEBUG", help="Python logging level")
parser.add_argument(
    "-b", "--batch", default=None, help="Only process a specific image batch"
)
parser.add_argument(
    "--download", help="Download images from server", action="store_true", default=False
)

parser.add_argument("-m", "--monitor", action="store_true", default=False)
parser.add_argument(
    "--emailrecipients",
    default=None,
    help="Spaceless comma-separated values of email recipients",
)
parser.add_argument(
    "--emailsender",
    default=None,
    help="One email sender",
)
parser.add_argument(
    "--midwaypostprocesshours",
    default=16.0,
    help="Time, in hours, to wait before sending a summary email",
)
parser.add_argument(
    "--finalpostprocesshours",
    default=48.0,
    help="Time, in hours, to wait before ceasing monitoring for new images",
)
parser.add_argument(
    "--rawdir",
    default=raw_img_sub_dir,
    help="Subdirectory to look in for raw images of a given night",
)

args = parser.parse_args()

if args.download:

    Pipeline.pipelines[args.pipeline.lower()].download_raw_images_for_night(
        night=args.night
    )

    logger.info("Download complete")

night = args.night
if night is None:
    night = str(ln).split(" ", maxsplit=1)[0].replace("-", "")


try:

    if args.monitor:

        if args.emailrecipients is not None:
            EMAIL_RECIPIENTS = args.emailrecipients.split(",")
        else:
            EMAIL_RECIPIENTS = None

        CONFIG = args.config
        if CONFIG is None:
            CONFIG = "realtime"

        monitor = Monitor(
            pipeline=args.pipeline,
            night=night,
            realtime_configurations=CONFIG,
            postprocess_configurations=args.postprocessconfig.split(",")
            if args.postprocessconfig is not None
            else None,
            log_level=args.level,
            final_postprocess_hours=args.finalpostprocesshours,
            midway_postprocess_hours=args.midwaypostprocesshours,
            email_sender=args.emailsender,
            email_recipients=EMAIL_RECIPIENTS,
            raw_dir=args.rawdir,
        )
        monitor.process_realtime()

    else:

        # Set up logging

        log = logging.getLogger("winterdrp")

        if args.logfile is None:
            handler = logging.StreamHandler(sys.stdout)
        else:
            handler = logging.FileHandler(args.logfile)

        formatter = logging.Formatter(
            "%(name)s [l %(lineno)d] - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(args.level)

        CONFIG = args.config
        if CONFIG is None:
            CONFIG = "default"

        pipe = get_pipeline(
            args.pipeline,
            selected_configurations=CONFIG,
            night=night,
        )

        batches, errorstack = pipe.reduce_images(
            Dataset([ImageBatch()]), catch_all_errors=True
        )
        if args.postprocessconfig is not None:
            post_config = [
                x for x in pipe.set_configuration(CONFIG) if isinstance(x, ImageLoader)
            ][:1]
            post_config += pipe.postprocess_configuration(
                errorstack=errorstack,
                selected_configurations=args.postprocessconfig.split(","),
            )

            PROTECTED_KEY = "_new_postprocess"

            pipe.add_configuration(PROTECTED_KEY, post_config)
            pipe.set_configuration(PROTECTED_KEY)

            _, new_errorstack = pipe.reduce_images(
                Dataset([ImageBatch()]),
                selected_configurations=PROTECTED_KEY,
                catch_all_errors=True,
            )
            errorstack += new_errorstack

        print(errorstack.summarise_error_stack(verbose=False))
        errorstack.summarise_error_stack(
            output_path=pipe.get_error_output_path(), verbose=True
        )

        logger.info("End of winterdrp execution")

finally:
    # Delete everything added to the cache
    clean_cache()
