"""
Script containing the various
:class:`~winterdrp.processors.base_processor.BaseProcessor`
lists which are used to build configurations for the
:class:`~winterdrp.pipelines.sedmv2.sedmv2_pipeline.SEDMv2Pipeline`.
"""
from winterdrp.paths import BASE_NAME_KEY, core_fields
from winterdrp.pipelines.sedmv2.config import (
    psfex_config_path,
    sedmv2_cal_requirements,
    sedmv2_mask_path,
    sextractor_astrometry_config,
    sextractor_photometry_config,
    sextractor_reference_config,
    swarp_config_path,
)
from winterdrp.pipelines.sedmv2.generator import (
    sedmv2_photometric_catalog_generator,
    sedmv2_reference_image_generator,
    sedmv2_reference_image_resampler,
    sedmv2_reference_psfex,
    sedmv2_reference_sextractor,
)
from winterdrp.pipelines.sedmv2.load_sedmv2_image import load_raw_sedmv2_image, \
    load_proc_sedmv2_image
from winterdrp.processors import BiasCalibrator, FlatCalibrator
from winterdrp.processors.anet import AstrometryNet
from winterdrp.processors.astromatic import PSFex, Sextractor, Swarp
from winterdrp.processors.csvlog import CSVLog
from winterdrp.processors.mask import MaskPixels
from winterdrp.processors.photcal import PhotCalibrator
from winterdrp.processors.photometry.aperture_photometry import (
    CandidateAperturePhotometry,
    ImageAperturePhotometry,
)
from winterdrp.processors.photometry.psf_photometry import (
    CandidatePSFPhotometry,
    ImagePSFPhotometry,
)
from winterdrp.processors.reference import Reference
from winterdrp.processors.utils import (
    ImageBatcher,
    ImageLoader,
    ImageSaver,
    ImageSelector,
    MultiExtParser,
)
from winterdrp.processors.utils.cal_hunter import CalHunter
from winterdrp.processors.utils.header_annotate import HeaderEditor
from winterdrp.processors.zogy.zogy import (
    ZOGY,
    ZOGYPrepare,
    default_sedmv2_catalog_purifier,
)

load_raw = [
    MultiExtParser(input_sub_dir="raw/mef/"),
    ImageLoader(load_image=load_raw_sedmv2_image),
]

load_proc = [
    ImageLoader(load_image=load_proc_sedmv2_image),
]

cal_hunter = [
    CalHunter(load_image=load_raw_sedmv2_image, requirements=sedmv2_cal_requirements),
]

build_log = [  # pylint: disable=duplicate-code
    CSVLog(
        export_keys=[
            "UTC",
            "FIELDID",
            "FILTERID",
            "OBSTYPE",
            "RA",
            "DEC",
            "PROGID",
            BASE_NAME_KEY,
        ]
        + core_fields
    ),
]  # pylint: disable=duplicate-code

reduce = [
    BiasCalibrator(),
    ImageSelector(("OBSTYPE", ["FLAT", "SCIENCE"])),
    ImageBatcher(split_key="filter"),
    FlatCalibrator(),
    ImageBatcher(split_key=BASE_NAME_KEY),
    ImageSelector(("OBSTYPE", ["SCIENCE"])),  # pylint: disable=duplicate-code
    ImageSaver(output_dir_name="detrend", write_mask=True),
    AstrometryNet(
        output_sub_dir="a-net",
        scale_bounds=(0.1667, 0.0333),
        scale_units="degw",
        downsample=2,
        timeout=900,
    ),
    MaskPixels(mask_path=sedmv2_mask_path),
    Sextractor(
        output_sub_dir="sextractor",
        checkimage_name=None,
        checkimage_type=None,
        **sextractor_astrometry_config
    ),
]

resample = [
    Swarp(
        swarp_config_path=swarp_config_path,
        include_scamp=False,
        combine=False,
        calculate_dims_in_swarp=True,
    ),
    ImageSaver(
        output_dir_name="resampled", write_mask=True
    ),  # pylint: disable=duplicate-code
]

calibrate = [
    Sextractor(
        output_sub_dir="photprocess",
        checkimage_type="BACKGROUND_RMS",
        **sextractor_photometry_config
    ),  # pylint: disable=duplicate-code
    PhotCalibrator(ref_catalog_generator=sedmv2_photometric_catalog_generator),
    ImageSaver(
        output_dir_name="processed",
        write_mask=True,
    ),
    HeaderEditor(edit_keys="procflag", values=1),
]

process = reduce + resample + calibrate


# stellar --

parse_stellar = [ImageSelector(("SOURCE", ["stellar", "None"]))]

process_stellar = parse_stellar + process

image_photometry = [  # imported from wirc/blocks.py
    ImageSelector(("SOURCE", "stellar")),
    ImageAperturePhotometry(
        aper_diameters=[16],
        bkg_in_diameters=[25],
        bkg_out_diameters=[40],
        col_suffix_list=[""],
        phot_cutout_size=100,
        target_ra_key="TARGRA",
        target_dec_key="TARGDEC",
    ),
    Sextractor(**sextractor_reference_config, output_sub_dir="subtract", cache=False),
    PSFex(config_path=psfex_config_path, output_sub_dir="photometry", norm_fits=True),
    ImagePSFPhotometry(target_ra_key="TARGRA", target_dec_key="TARGDEC"),
    ImageSaver(output_dir_name="photometry"),
]

candidate_photometry = [  # imported from wirc/blocks.py
    CandidateAperturePhotometry(
        aper_diameters=[16, 70],
        phot_cutout_size=100,
        bkg_in_diameters=[25, 90],
        bkg_out_diameters=[40, 100],
        col_suffix_list=["", "big"],
    ),
    CandidatePSFPhotometry(),
]


# transients --

parse_transient = [ImageSelector(("SOURCE", ["transient", "None"]))]

resample_transient = [
    Swarp(
        swarp_config_path=swarp_config_path,
        include_scamp=False,
        combine=True,
    ),
    ImageSaver(
        output_dir_name="resampled", write_mask=True
    ),  # pylint: disable=duplicate-code
]

process_transient = parse_transient + reduce + resample_transient + calibrate

subtract = [
    ImageBatcher(split_key=BASE_NAME_KEY),
    ImageSelector(("OBSTYPE", "SCIENCE")),
    Reference(
        ref_image_generator=sedmv2_reference_image_generator,
        ref_psfex=sedmv2_reference_psfex,
        sextractor=sedmv2_reference_sextractor,
        swarp_resampler=sedmv2_reference_image_resampler,  # pylint: disable=duplicate-code
    ),
    Sextractor(
        output_sub_dir="subtract",
        cache=True,
        write_regions_bool=True,
        **sextractor_photometry_config
    ),
    PSFex(config_path=psfex_config_path, output_sub_dir="subtract", norm_fits=True),
    # ImageSaver(output_dir_name="ref"),
    ZOGYPrepare(
        output_sub_dir="subtract",
        sci_zp_header_key="ZP_AUTO",
        catalog_purifier=default_sedmv2_catalog_purifier,
        write_region_bool=True
    ),
    ZOGY(output_sub_dir="subtract",
         sci_zp_header_key="ZP_AUTO",),
]

imsub = subtract  # + export_diff_to_db + extract_candidates
