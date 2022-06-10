import os
import numpy as np
import logging
import astropy.io.fits
from winterdrp.processors.astromatic.sextractor.sourceextractor import run_sextractor_single, default_saturation
from winterdrp.processors.base_processor import BaseProcessor
from winterdrp.paths import get_output_dir, get_temp_path, latest_mask_save_key

logger = logging.getLogger(__name__)

sextractor_header_key = 'SRCCAT'


class Sextractor(BaseProcessor):
    base_key = "sextractor"

    def __init__(
            self,
            output_sub_dir: str,
            config_path: str,
            parameter_path: str,
            filter_path: str,
            starnnw_path: str,
            saturation: float = default_saturation,
            verbose_type: str = "QUIET",
            checkimage_name: str | list = None,
            checkimage_type: str | list = None,
            gain: float = None,
            *args,
            **kwargs
    ):
        super(Sextractor, self).__init__(*args, **kwargs)
        self.output_sub_dir = output_sub_dir
        self.config = config_path

        self.parameters_name = parameter_path
        self.filter_name = filter_path
        self.starnnw_name = starnnw_path
        self.saturation = saturation
        self.verbose_type = verbose_type
        self.checkimage_name = checkimage_name
        self.checkimage_type = checkimage_type
        self.gain = gain

    def get_sextractor_output_dir(self):
        return get_output_dir(self.output_sub_dir, self.night_sub_dir)

    def _apply_to_images(
            self,
            images: list[np.ndarray],
            headers: list[astropy.io.fits.Header],
    ) -> tuple[list[np.ndarray], list[astropy.io.fits.Header]]:

        sextractor_out_dir = self.get_sextractor_output_dir()

        try:
            os.makedirs(sextractor_out_dir)
        except OSError:
            pass

        for i, data in enumerate(images):
            header = headers[i]

            temp_path = get_temp_path(sextractor_out_dir, header["BASENAME"])

            mask_path = None
            if latest_mask_save_key in header.keys():
                mask_path = get_temp_path(sextractor_out_dir, header[latest_mask_save_key])
                if not os.path.exists(mask_path):
                    mask_path = None

            if mask_path is None:
                self.save_fits(data, header, temp_path)
                mask_path = self.save_mask(data, header, temp_path)

            output_cat = os.path.join(sextractor_out_dir, header["BASENAME"].replace(".fits", ".cat"))

            output_cat = run_sextractor_single(
                img=temp_path,
                config=self.config,
                output_dir=sextractor_out_dir,
                parameters_name=self.parameters_name,
                filter_name=self.filter_name,
                starnnw_name=self.starnnw_name,
                saturation=self.saturation,
                weight_image=mask_path,
                verbose_type=self.verbose_type,
                checkimage_name=self.checkimage_name,
                checkimage_type=self.checkimage_type,
                gain=self.gain,
                catalog_name=output_cat
            )

            os.remove(temp_path)
            logger.info(f"Deleted temporary image {temp_path}")

            header[sextractor_header_key] = os.path.join(sextractor_out_dir, output_cat)

        return images, headers
