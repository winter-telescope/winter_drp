"""
Module for WINTER data reduction
"""

# pylint: disable=duplicate-code
from mirar.catalog.kowalski import PS1, TMASS
from mirar.downloader.get_test_data import get_test_data_dir
from mirar.paths import (
    BASE_NAME_KEY,
    DITHER_N_KEY,
    EXPTIME_KEY,
    FITS_MASK_KEY,
    LATEST_SAVE_KEY,
    MAX_DITHER_KEY,
    OBSCLASS_KEY,
    RAW_IMG_KEY,
    SOURCE_HISTORY_KEY,
    SOURCE_NAME_KEY,
    TARGET_KEY,
    ZP_KEY,
    base_output_dir,
)
from mirar.pipelines.winter.config import (
    prv_candidate_cols,
    psfex_path,
    scamp_config_path,
    sextractor_astrometry_config,
    sextractor_astromstats_config,
    sextractor_candidate_config,
    sextractor_photometry_config,
    sextractor_photometry_psf_config,
    sextractor_reference_psf_phot_config,
    swarp_config_path,
    winter_avro_schema_path,
    winter_fritz_config,
)
from mirar.pipelines.winter.constants import NXSPLIT, NYSPLIT
from mirar.pipelines.winter.generator import (
    mask_stamps_around_bright_stars,
    select_winter_flat_images,
    winter_anet_sextractor_config_path_generator,
    winter_astrometric_ref_catalog_generator,
    winter_astrometric_ref_catalog_namer,
    winter_astrometry_sextractor_catalog_purifier,
    winter_astrostat_catalog_purifier,
    winter_cal_requirements,
    winter_candidate_annotator_filterer,
    winter_candidate_avro_fields_calculator,
    winter_candidate_quality_filterer,
    winter_fourier_filtered_image_generator,
    winter_history_deprecated_constraint,
    winter_imsub_catalog_purifier,
    winter_new_source_updater,
    winter_photcal_color_columns_generator,
    winter_photometric_catalog_generator,
    winter_photometric_catalogs_purifier,
    winter_photometric_ref_catalog_namer,
    winter_reference_generator,
    winter_reference_image_resampler_for_zogy,
    winter_reference_psf_phot_sextractor,
    winter_reference_psfex,
    winter_reference_sextractor,
    winter_skyportal_annotator,
    winter_source_entry_updater,
    winter_stackid_annotator,
)
from mirar.pipelines.winter.load_winter_image import (
    annotate_winter_subdet_headers,
    get_raw_winter_mask,
    load_test_winter_image,
    load_winter_mef_image,
    load_winter_stack,
)
from mirar.pipelines.winter.models import (
    DEFAULT_FIELD,
    NAME_START,
    SOURCE_PREFIX,
    AstrometryStat,
    Candidate,
    Diff,
    Exposure,
    FirstPassAstrometryStat,
    Raw,
    Source,
    Stack,
)
from mirar.pipelines.winter.validator import (
    masked_images_rejector,
    poor_astrometric_quality_rejector,
    winter_dark_oversubtraction_rejector,
)
from mirar.processors.astromatic import PSFex, Scamp
from mirar.processors.astromatic.scamp.scamp import SCAMP_HEADER_KEY
from mirar.processors.astromatic.sextractor.background_subtractor import (
    SextractorBkgSubtractor,
)
from mirar.processors.astromatic.sextractor.sextractor import (
    Sextractor,
    sextractor_checkimg_map,
)
from mirar.processors.astromatic.swarp import ReloadSwarpComponentImages
from mirar.processors.astromatic.swarp.swarp import Swarp
from mirar.processors.astrometry.anet.anet_processor import AstrometryNet
from mirar.processors.astrometry.utils import AstrometryFromFile
from mirar.processors.astrometry.validate import AstrometryStatsWriter
from mirar.processors.avro import IPACAvroExporter
from mirar.processors.catalog_limiting_mag import CatalogLimitingMagnitudeCalculator
from mirar.processors.csvlog import CSVLog
from mirar.processors.dark import DarkCalibrator
from mirar.processors.database.database_inserter import (
    DatabaseImageBatchInserter,
    DatabaseImageInserter,
    DatabaseSourceInserter,
)
from mirar.processors.database.database_selector import (
    SelectSourcesWithMetadata,
    SingleSpatialCrossmatchSource,
)
from mirar.processors.database.database_updater import ImageDatabaseMultiEntryUpdater
from mirar.processors.flat import FlatCalibrator, SkyFlatCalibrator
from mirar.processors.mask import (  # MaskAboveThreshold,
    MaskDatasecPixels,
    MaskPixelsFromFunction,
    MaskPixelsFromPathInverted,
    MaskPixelsFromWCS,
    WriteMaskedCoordsToFile,
)
from mirar.processors.photcal import ZPWithColorTermCalculator
from mirar.processors.photcal.photcalibrator import PhotCalibrator
from mirar.processors.photometry import AperturePhotometry, PSFPhotometry
from mirar.processors.reference import GetReferenceImage, ProcessReference
from mirar.processors.skyportal.skyportal_candidate import SkyportalCandidateUploader
from mirar.processors.sources import (
    CandidateNamer,
    CustomSourceTableModifier,
    ForcedPhotometryDetector,
    SourceLoader,
    SourceWriter,
    ZOGYSourceDetector,
)
from mirar.processors.split import SUB_ID_KEY, SplitImage, SwarpImageSplitter
from mirar.processors.utils import (
    CustomImageBatchModifier,
    HeaderAnnotator,
    ImageBatcher,
    ImageDebatcher,
    ImageLoader,
    ImagePlotter,
    ImageRejector,
    ImageSaver,
    ImageSelector,
    MEFLoader,
)
from mirar.processors.utils.cal_hunter import CalHunter
from mirar.processors.utils.image_loader import LoadImageFromHeader
from mirar.processors.xmatch import XMatch
from mirar.processors.zogy.reference_aligner import AlignReference
from mirar.processors.zogy.zogy import ZOGY, ZOGYPrepare

build_test = [
    MEFLoader(
        input_sub_dir="raw",
        load_image=load_winter_mef_image,
    ),
    ImageBatcher("UTCTIME"),
    CSVLog(
        export_keys=[
            "UTCTIME",
            "PROGNAME",
            DITHER_N_KEY,
            MAX_DITHER_KEY,
            "FILTER",
            EXPTIME_KEY,
            OBSCLASS_KEY,
            "BOARD_ID",
            "BASENAME",
            TARGET_KEY,
            "RADEG",
            "DECDEG",
            "T_ROIC",
            "FIELDID",
            "FOCPOS",
        ]
    ),
    ImageSelector(
        ("BOARD_ID", "2"),
        (OBSCLASS_KEY, ["dark", "science"]),
        (EXPTIME_KEY, "120.0"),
        ("filter", ["dark", "J"]),
        ("FIELDID", ["3944", str(DEFAULT_FIELD)]),
    ),
    ImageSaver("testdata", output_dir=get_test_data_dir()),
]

load_test = [
    ImageLoader(
        input_img_dir=get_test_data_dir(),
        input_sub_dir="raw",
        load_image=load_test_winter_image,
    ),
    ImageBatcher("UTCTIME"),
]

refbuild = [
    GetReferenceImage(ref_image_generator=winter_reference_generator),
    ImageSaver(output_dir_name="stacked_ref"),
]

# Start for new WINTER blocks:

load_raw = [
    MEFLoader(
        input_sub_dir="raw",
        load_image=load_winter_mef_image,
    ),
]

extract_all = [
    ImageBatcher("UTCTIME"),
    DatabaseImageBatchInserter(db_table=Exposure, duplicate_protocol="replace"),
    ImageSelector((OBSCLASS_KEY, ["dark", "science", "flat"])),
]

csvlog = [
    CSVLog(
        export_keys=[
            "UTCTIME",
            "PROGNAME",
            DITHER_N_KEY,
            MAX_DITHER_KEY,
            "FILTER",
            EXPTIME_KEY,
            OBSCLASS_KEY,
            "BOARD_ID",
            "BASENAME",
            TARGET_KEY,
            "RADEG",
            "DECDEG",
            "T_ROIC",
            "FIELDID",
        ]
    ),
]

select_split_subset = [ImageSelector(("SUBCOORD", "0_0"))]

# Optional subset selection
BOARD_ID = 4
select_subset = [
    ImageSelector(
        ("BOARD_ID", str(BOARD_ID)),
    ),
]

select_ref = [
    ImageSelector(
        ("FIELDID", str(3944)),
        ("BOARD_ID", str(BOARD_ID)),
    ),
    ImageDebatcher(),
    ImageBatcher("STACKID"),
]

# mask
mask = [
    ImageBatcher(BASE_NAME_KEY),
    # MaskAboveThreshold(threshold=40000.0),
    MaskDatasecPixels(),
    MaskPixelsFromFunction(mask_function=get_raw_winter_mask),
]

# Split
split = [
    SplitImage(n_x=NXSPLIT, n_y=NYSPLIT),
    CustomImageBatchModifier(annotate_winter_subdet_headers),
]

mask_and_split = mask + split

# Save raw images

save_raw = [
    ImageSaver(output_dir_name="raw_unpacked", write_mask=False),
    DatabaseImageInserter(db_table=Raw, duplicate_protocol="replace"),
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "FILTER", "EXPTIME", TARGET_KEY, "SUBCOORD"]),
    CustomImageBatchModifier(winter_stackid_annotator),
    ImageSaver(output_dir_name="raw_unpacked", write_mask=False),
    HeaderAnnotator(input_keys=LATEST_SAVE_KEY, output_key=RAW_IMG_KEY),
    ImageRejector(("BOARD_ID", "0")),
]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Various processing steps

# Load from unpacked dir

load_unpacked = [
    ImageLoader(input_sub_dir="raw_unpacked", input_img_dir=base_output_dir),
    HeaderAnnotator(input_keys=LATEST_SAVE_KEY, output_key=RAW_IMG_KEY),
    ImageRejector(("BOARD_ID", "0")),
    ImageDebatcher(),
    ImageBatcher("UTCTIME"),
    CSVLog(
        export_keys=[
            "UTCTIME",
            "PROGNAME",
            DITHER_N_KEY,
            MAX_DITHER_KEY,
            "FILTER",
            EXPTIME_KEY,
            OBSCLASS_KEY,
            "BOARD_ID",
            "BASENAME",
            TARGET_KEY,
            "RADEG",
            "DECDEG",
            "T_ROIC",
            "FIELDID",
            "MEDCOUNT",
        ]
    ),
    DatabaseImageInserter(db_table=Raw, duplicate_protocol="replace"),
    ImageRejector(("BOARD_ID", "0")),
]

# Calibration hunter
cal_hunter = [
    CalHunter(load_image=load_winter_mef_image, requirements=winter_cal_requirements)
]

# Detrend blocks
dark_calibrate = [
    ImageDebatcher(),
    ImageBatcher(
        ["BOARD_ID", EXPTIME_KEY, "SUBCOORD", "GAINCOLT", "GAINCOLB", "GAINROW"]
    ),
    DarkCalibrator(
        cache_sub_dir="calibration_darks",
        cache_image_name_header_keys=[EXPTIME_KEY, "BOARD_ID"],
    ),
    ImageSelector((OBSCLASS_KEY, ["science", "flat"])),
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "UTCTIME", "SUBCOORD"]),
    ImageSaver(output_dir_name="darkcal"),
    HeaderAnnotator(input_keys=LATEST_SAVE_KEY, output_key=RAW_IMG_KEY),
    CustomImageBatchModifier(winter_dark_oversubtraction_rejector),
]

# First pass flat calibration
first_pass_flat_calibrate = [
    ImageDebatcher(),
    ImageBatcher(
        [
            "BOARD_ID",
            "FILTER",
            "SUBCOORD",
            "GAINCOLT",
            "GAINCOLB",
            "GAINROW",
        ]
    ),
    FlatCalibrator(
        cache_sub_dir="fp_flats",
        select_flat_images=select_winter_flat_images,
        cache_image_name_header_keys=["FILTER", "BOARD_ID"],
    ),
    ImageSaver(output_dir_name="skyflatcal"),
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "UTCTIME", "SUBCOORD"]),
    Sextractor(
        **sextractor_astrometry_config,
        write_regions_bool=True,
        output_sub_dir="fp_skysub",
        checkimage_type=["-BACKGROUND"],
    ),
    SextractorBkgSubtractor(),
    ImageSaver(output_dir_name="fp_skysub"),
]

# Fourier filtering
fourier_filter = [
    CustomImageBatchModifier(winter_fourier_filtered_image_generator),
]

# Various astrometry-related blocks
astrometry_net = [
    ImageDebatcher(),
    ImageBatcher(["UTCTIME", "BOARD_ID", "SUBCOORD"]),
    AstrometryNet(
        output_sub_dir="anet",
        scale_bounds=[1.0, 1.3],
        scale_units="app",
        use_sextractor=True,
        parity="neg",
        search_radius_deg=5.0,
        sextractor_config_path=winter_anet_sextractor_config_path_generator,
        use_weight=True,
        timeout=120,
        cache=True,
    ),
]

astrometry_scamp = [
    ImageDebatcher(),
    ImageBatcher(
        [TARGET_KEY, "FILTER", EXPTIME_KEY, "BOARD_ID", "SUBCOORD", "DITHGRP"]
    ),
    Sextractor(
        **sextractor_astrometry_config,
        write_regions_bool=True,
        output_sub_dir="scamp",
        catalog_purifier=winter_astrometry_sextractor_catalog_purifier,
    ),
    CustomImageBatchModifier(winter_astrometric_ref_catalog_namer),
    Scamp(
        scamp_config_path=scamp_config_path,
        ref_catalog_generator=winter_astrometric_ref_catalog_generator,
        copy_scamp_header_to_image=True,
        cache=True,
    ),
]

validate_astrometry = [
    ImageDebatcher(),
    ImageBatcher(["UTCTIME", "BOARD_ID", "SUBCOORD"]),
    Sextractor(
        **sextractor_astromstats_config,
        write_regions_bool=True,
        output_sub_dir="astrostats",
    ),
    AstrometryStatsWriter(
        ref_catalog_generator=winter_astrometric_ref_catalog_generator,
        image_catalog_purifier=winter_astrostat_catalog_purifier,
        write_regions=True,
        cache=False,
        crossmatch_radius_arcsec=5.0,
    ),
]

first_pass_validate_astrometry_export_and_filter = validate_astrometry + [
    DatabaseImageInserter(
        db_table=FirstPassAstrometryStat, duplicate_protocol="replace"
    ),
    CustomImageBatchModifier(poor_astrometric_quality_rejector),
]

second_pass_validate_astrometry_export_and_filter = validate_astrometry + [
    DatabaseImageInserter(db_table=AstrometryStat, duplicate_protocol="replace"),
    CustomImageBatchModifier(poor_astrometric_quality_rejector),
]

load_calibrated = [
    ImageLoader(input_sub_dir="skysub", input_img_dir=base_output_dir),
    ImageBatcher(["UTCTIME", "BOARD_ID"]),
]

# Stacking
stack_dithers = [
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "FILTER", "EXPTIME", TARGET_KEY, "SUBCOORD"]),
    Swarp(
        swarp_config_path=swarp_config_path,
        calculate_dims_in_swarp=True,
        include_scamp=True,
        subtract_bkg=False,
        cache=False,
        center_type="ALL",
        temp_output_sub_dir="stacks_weights",
        header_keys_to_combine=["RAWID"],
    ),
]

first_pass_stacking = (
    astrometry_net
    + astrometry_scamp
    + first_pass_validate_astrometry_export_and_filter
    + [
        ImageSaver(output_dir_name="fp_post_astrometry"),
    ]
    + stack_dithers
    + [
        ImageSaver(output_dir_name="fp_stack"),
    ]
)

load_astrometried = [
    ImageLoader(
        input_sub_dir="fp_post_astrometry",
        input_img_dir=base_output_dir,
    )
]

# Second pass calibration
second_pass_calibration = [
    ImageLoader(
        input_sub_dir="fp_stack",
        input_img_dir=base_output_dir,
        load_image=load_winter_stack,
    ),
    Sextractor(
        output_sub_dir="sp_stack_source_mask",
        **sextractor_astrometry_config,
        checkimage_type="SEGMENTATION",
        cache=True,
    ),
    MaskPixelsFromPathInverted(
        mask_path_key=sextractor_checkimg_map["SEGMENTATION"],
        write_masked_pixels_to_file=True,
        output_dir="sp_stack_source_mask",
    ),
    WriteMaskedCoordsToFile(output_dir="sp_stack_mask"),
    ReloadSwarpComponentImages(
        copy_header_keys=FITS_MASK_KEY,
    ),
    LoadImageFromHeader(
        header_key=RAW_IMG_KEY,
        copy_header_keys=[SCAMP_HEADER_KEY, FITS_MASK_KEY],
    ),
    AstrometryFromFile(astrometry_file_key=SCAMP_HEADER_KEY),
    ImageSaver(output_dir_name="sp_astrometry", write_mask=True),
    MaskPixelsFromWCS(
        write_masked_pixels_to_file=True,
        output_dir="sp_source_mask",
        only_write_mask=True,
    ),
    ImageSaver(output_dir_name="sp_masked", write_mask=True),
    SkyFlatCalibrator(flat_mask_key=FITS_MASK_KEY),
    ImageSaver(output_dir_name="sp_calibration_flat"),
    Sextractor(
        **sextractor_astrometry_config,
        write_regions_bool=True,
        output_sub_dir="skysub",
        checkimage_type=["-BACKGROUND"],
    ),
    SextractorBkgSubtractor(),
    ImageSaver(output_dir_name="skysub"),
]

# Second pass astrometry
second_pass_astrometry = (
    astrometry_net
    + [
        ImageSaver(output_dir_name="post_anet"),
    ]
    + astrometry_scamp
    + [
        ImageSaver(output_dir_name="post_scamp"),
    ]
)

# Second pass stacking
second_pass_stack = (
    second_pass_astrometry
    + second_pass_validate_astrometry_export_and_filter
    + stack_dithers
    + [
        ImageSaver(output_dir_name="stack"),
    ]
)

# Photometric calibration
photcal_and_export = [
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "FILTER", TARGET_KEY, "SUBCOORD"]),
    HeaderAnnotator(input_keys=LATEST_SAVE_KEY, output_key=RAW_IMG_KEY),
    CustomImageBatchModifier(masked_images_rejector),
    Sextractor(
        **sextractor_photometry_config,
        output_sub_dir="stack_psf",
        checkimage_type="BACKGROUND_RMS",
    ),
    PSFex(config_path=psfex_path, output_sub_dir="phot", norm_fits=True),
    Sextractor(
        **sextractor_photometry_psf_config,
        output_sub_dir="phot",
        checkimage_type="BACKGROUND_RMS",
        use_psfex=True,
    ),
    CustomImageBatchModifier(winter_photometric_ref_catalog_namer),
    PhotCalibrator(
        ref_catalog_generator=winter_photometric_catalog_generator,
        catalogs_purifier=winter_photometric_catalogs_purifier,
        temp_output_sub_dir="phot",
        write_regions=True,
        cache=True,
        zp_calculator=ZPWithColorTermCalculator(
            color_colnames_guess_generator=winter_photcal_color_columns_generator,
            reject_outliers=True,
            solver="curve_fit",
        ),
        zp_column_name="MAG_AUTO",
    ),
    CatalogLimitingMagnitudeCalculator(
        sextractor_mag_key_name="MAG_AUTO", write_regions=True
    ),
    AstrometryStatsWriter(
        ref_catalog_generator=winter_astrometric_ref_catalog_generator,
        image_catalog_purifier=winter_astrostat_catalog_purifier,
        write_regions=True,
        cache=False,
        crossmatch_radius_arcsec=5.0,
    ),
    ImageSaver(output_dir_name="final"),
    DatabaseImageInserter(db_table=Stack, duplicate_protocol="replace"),
    ImageDatabaseMultiEntryUpdater(
        sequence_key="rawid",
        db_table=Raw,
        db_alter_columns="ustackid",
    ),
    ImagePlotter(
        output_sub_dir="final_stacks_plots",
        annotate_fields=[
            BASE_NAME_KEY,
            "COADDS",
            TARGET_KEY,
            "CRVAL1",
            "CRVAL2",
            "FILTER",
            "ZP",
            "ZPSTD",
        ],
    ),
]
# End of image-reduction blocks

# Image subtraction

load_final_stack = [
    ImageLoader(
        input_sub_dir="final",
        input_img_dir=base_output_dir,
        load_image=load_winter_stack,
    ),
    DatabaseImageInserter(db_table=Stack, duplicate_protocol="ignore"),
]

plot_stack = [
    ImageDebatcher(),
    ImageBatcher([TARGET_KEY, "BOARD_ID"]),
    ImagePlotter(
        output_sub_dir="final_stacks_plots",
        annotate_fields=[
            BASE_NAME_KEY,
            "COADDS",
            TARGET_KEY,
            "CRVAL1",
            "CRVAL2",
            "FILTER",
            "ZP",
            "ZPSTD",
        ],
    ),
]

split_stack = [
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "FILTER", TARGET_KEY, "SUBCOORD", "STACKID"]),
    SwarpImageSplitter(swarp_config_path=swarp_config_path, n_x=2, n_y=1),
    ImageSaver(output_dir_name="split_stacks"),
]

imsub = [
    ImageDebatcher(),
    ImageBatcher(["BOARD_ID", "FILTER", TARGET_KEY, "SUBCOORD", "STACKID"]),
    HeaderAnnotator(input_keys=[SUB_ID_KEY], output_key="SUBDETID"),
    ProcessReference(
        ref_image_generator=winter_reference_generator,
        swarp_resampler=winter_reference_image_resampler_for_zogy,
        sextractor=winter_reference_sextractor,
        ref_psfex=winter_reference_psfex,
        phot_sextractor=winter_reference_psf_phot_sextractor,
    ),
    Sextractor(
        **sextractor_reference_psf_phot_config,
        output_sub_dir="subtract",
        cache=False,
        use_psfex=True,
    ),
    PSFex(config_path=psfex_path, output_sub_dir="subtract", norm_fits=True),
    AlignReference(
        order=1,
        sextractor=winter_reference_sextractor,
        psfex=winter_reference_psfex,
        phot_sextractor=winter_reference_psf_phot_sextractor,
        catalog_purifier=winter_imsub_catalog_purifier,
    ),
    MaskPixelsFromFunction(mask_function=mask_stamps_around_bright_stars),
    ImageSaver(output_dir_name="presubtract"),
    ZOGYPrepare(
        output_sub_dir="subtract",
        sci_zp_header_key="ZP_AUTO",
        ref_zp_header_key=ZP_KEY,
        catalog_purifier=winter_imsub_catalog_purifier,
        x_key="XMODEL_IMAGE",
        y_key="YMODEL_IMAGE",
        flux_key="FLUX_POINTSOURCE",
    ),
    # ImageSaver(output_dir_name="prezogy"),
    ZOGY(
        output_sub_dir="subtract", sci_zp_header_key="ZP_AUTO", ref_zp_header_key=ZP_KEY
    ),
    ImageSaver(output_dir_name="diffs"),
    DatabaseImageInserter(db_table=Diff, duplicate_protocol="replace"),
    ImageSaver(output_dir_name="subtract"),
]

load_sub = [
    ImageLoader(input_sub_dir="subtract"),
]
detect_candidates = [
    ZOGYSourceDetector(
        output_sub_dir="subtract",
        **sextractor_candidate_config,
        write_regions=True,
        detect_negative_sources=True,
    ),
    PSFPhotometry(phot_cutout_half_size=10),
    AperturePhotometry(
        temp_output_sub_dir="aper_photometry",
        aper_diameters=[8, 16],
        phot_cutout_half_size=50,
        bkg_in_diameters=[25, 25],
        bkg_out_diameters=[40, 40],
        col_suffix_list=["", "big"],
    ),
    CustomSourceTableModifier(winter_candidate_annotator_filterer),
    SourceWriter(output_dir_name="candidates"),
]

load_sources = [
    SourceLoader(input_dir_name="candidates"),
]

crossmatch_candidates = [
    XMatch(catalog=TMASS(num_sources=3, search_radius_arcmin=0.5)),
    XMatch(catalog=PS1(num_sources=3, search_radius_arcmin=0.5)),
    SourceWriter(output_dir_name="kowalski"),
    CustomSourceTableModifier(
        modifier_function=winter_candidate_avro_fields_calculator
    ),
]

select_history = [
    SelectSourcesWithMetadata(
        db_query_columns=["sourceid"],
        db_table=Candidate,
        db_output_columns=prv_candidate_cols + [SOURCE_NAME_KEY],
        base_output_column=SOURCE_HISTORY_KEY,
        additional_query_constraints=winter_history_deprecated_constraint,
    ),
]

name_candidates = (
    [
        # Check if the source is already in the source table
        SingleSpatialCrossmatchSource(
            db_table=Source,
            db_output_columns=["sourceid", SOURCE_NAME_KEY],
            crossmatch_radius_arcsec=2.0,
            ra_field_name="average_ra",
            dec_field_name="average_dec",
        ),
        # Assign names to the new sources
        CandidateNamer(
            db_table=Source,
            base_name=SOURCE_PREFIX,
            name_start=NAME_START,
            db_name_field=SOURCE_NAME_KEY,
        ),
        # Add the new sources to the source table
        CustomSourceTableModifier(modifier_function=winter_new_source_updater),
        DatabaseSourceInserter(
            db_table=Source,
            duplicate_protocol="ignore",
        ),
        # Get all candidates associated with source
    ]
    + select_history
    + [
        # Update average ra and dec for source
        CustomSourceTableModifier(modifier_function=winter_source_entry_updater),
        # Update sources in the source table
        DatabaseSourceInserter(
            db_table=Source,
            duplicate_protocol="replace",
        ),
        # Add candidates in the candidate table
        DatabaseSourceInserter(
            db_table=Candidate,
            duplicate_protocol="fail",
        ),
        SourceWriter(output_dir_name="preavro"),
    ]
)

avro_export = [
    IPACAvroExporter(
        topic_prefix="winter",
        base_name="WNTR",
        broadcast=False,
        avro_schema_path=winter_avro_schema_path,
    ),
    CustomSourceTableModifier(modifier_function=winter_candidate_quality_filterer),
    SourceWriter(output_dir_name="preskyportal"),
]

process_candidates = crossmatch_candidates + name_candidates + avro_export

load_skyportal = [SourceLoader(input_dir_name="preskyportal")]

send_to_skyportal = [
    CustomSourceTableModifier(modifier_function=winter_skyportal_annotator),
    SkyportalCandidateUploader(**winter_fritz_config),
]

# To make a mosaic by stacking all boards
stack_boards = [
    ImageBatcher([TARGET_KEY]),
    Swarp(
        swarp_config_path=swarp_config_path,
        calculate_dims_in_swarp=True,
        include_scamp=False,
        subtract_bkg=False,
        cache=False,
        center_type="ALL",
        temp_output_sub_dir="mosaic_weights",
    ),
    ImageSaver(output_dir_name="mosaic"),
]

mosaic = load_final_stack + stack_boards

# To make cals for focusing
focus_subcoord = [
    HeaderAnnotator(input_keys=["BOARD_ID"], output_key="SUBCOORD"),
    HeaderAnnotator(input_keys=["BOARD_ID"], output_key="SUBDETID"),
]

# Combinations of different blocks, to be used in configurations
process_and_stack = (
    second_pass_astrometry
    + second_pass_validate_astrometry_export_and_filter
    + stack_dithers
    + [
        ImageSaver(output_dir_name="stack"),
    ]
)

unpack_subset = (
    load_raw
    + cal_hunter
    + extract_all
    + csvlog
    + select_subset
    + mask_and_split
    + save_raw
)

unpack_all = load_raw + cal_hunter + extract_all + csvlog + mask_and_split + save_raw

unpack_subset_no_calhunter = (
    load_raw + extract_all + csvlog + select_subset + mask_and_split + save_raw
)

unpack_all_no_calhunter = load_raw + extract_all + csvlog + mask_and_split + save_raw

second_pass_processing = (
    load_astrometried + stack_dithers + second_pass_calibration + second_pass_stack
)

first_pass_processing = (
    load_unpacked
    + dark_calibrate
    + first_pass_flat_calibrate
    + fourier_filter
    + first_pass_stacking
)

full_reduction = (
    dark_calibrate
    + first_pass_flat_calibrate
    + fourier_filter
    + first_pass_stacking
    + second_pass_calibration
    + fourier_filter
    + second_pass_stack
    + photcal_and_export
)

photcal_stacks = [
    ImageLoader(
        input_sub_dir="stack",
        input_img_dir=base_output_dir,
        load_image=load_winter_stack,
    ),
] + photcal_and_export

reduce_unpacked = load_unpacked + full_reduction

reduce = unpack_all + full_reduction

reduce_no_calhunter = unpack_all_no_calhunter + full_reduction

reftest = (
    unpack_subset
    + dark_calibrate
    + first_pass_flat_calibrate
    + process_and_stack
    + select_ref
    + refbuild
)

detrend_unpacked = load_unpacked + dark_calibrate + first_pass_flat_calibrate

realtime = extract_all + mask_and_split + save_raw + full_reduction

candidates = detect_candidates + process_candidates

full = realtime + imsub

focus_cals = (
    load_raw
    + extract_all
    + mask
    + focus_subcoord
    + csvlog
    + dark_calibrate
    + first_pass_flat_calibrate
)

stack_forced_photometry = [
    ImageDebatcher(),
    ImageBatcher([BASE_NAME_KEY]),
    ForcedPhotometryDetector(ra_header_key="TARGRA", dec_header_key="TARGDEC"),
    AperturePhotometry(
        aper_diameters=[5, 8, 10, 15],
        phot_cutout_half_size=50,
        bkg_in_diameters=[20, 20, 20, 20],
        bkg_out_diameters=[40, 40, 40, 40],
    ),
]

diff_forced_photometry = [
    ImageDebatcher(),
    ImageBatcher([BASE_NAME_KEY]),
    ForcedPhotometryDetector(ra_header_key="TARGRA", dec_header_key="TARGDEC"),
    AperturePhotometry(
        aper_diameters=[5, 8, 10, 15],
        phot_cutout_half_size=50,
        bkg_in_diameters=[20, 20, 20, 20],
        bkg_out_diameters=[40, 40, 40, 40],
    ),
    PSFPhotometry(),
]

perform_astrometry = load_calibrated + fourier_filter + second_pass_astrometry
