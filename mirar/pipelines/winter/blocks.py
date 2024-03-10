"""
Module with blocks for WINTER data reduction
"""

# pylint: disable=duplicate-code
from mirar.downloader.get_test_data import get_test_data_dir
from mirar.paths import (
    BASE_NAME_KEY,
    DITHER_N_KEY,
    EXPTIME_KEY,
    MAX_DITHER_KEY,
    OBSCLASS_KEY,
    TARGET_KEY,
)
from mirar.pipelines.winter.blocks_reduction import (
    cal_hunter,
    csvlog,
    dark_calibrate,
    extract_all,
    first_pass_flat_calibrate,
    first_pass_stacking,
    focus_subcoord,
    fourier_filter,
    load_astrometried,
    load_calibrated,
    load_raw,
    load_unpacked,
    mask,
    mask_and_split,
    photcal_and_export,
    save_raw,
    second_pass_astrometry,
    second_pass_calibration,
    second_pass_stack,
    second_pass_validate_astrometry_export_and_filter,
    select_subset,
    stack_dithers,
)
from mirar.pipelines.winter.blocks_subtraction import (
    detect_candidates,
    imsub,
    process_candidates,
    refbuild,
)
from mirar.pipelines.winter.load_winter_image import (
    load_test_winter_image,
    load_winter_mef_image,
)
from mirar.pipelines.winter.models import DEFAULT_FIELD
from mirar.processors.csvlog import CSVLog
from mirar.processors.photometry import AperturePhotometry, PSFPhotometry
from mirar.processors.sources import ForcedPhotometryDetector
from mirar.processors.utils import (
    ImageBatcher,
    ImageDebatcher,
    ImageLoader,
    ImageSaver,
    ImageSelector,
    MEFLoader,
)

# Combinations of different blocks, to be used in configurations
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

first_pass_processing = (
    load_unpacked
    + dark_calibrate
    + first_pass_flat_calibrate
    + fourier_filter
    + first_pass_stacking
)

second_pass_processing = (
    load_astrometried + stack_dithers + second_pass_calibration + second_pass_stack
)

detrend_unpacked = load_unpacked + dark_calibrate + first_pass_flat_calibrate

perform_astrometry = load_calibrated + fourier_filter + second_pass_astrometry

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

reduce_unpacked = load_unpacked + full_reduction

reduce = unpack_all + full_reduction

reduce_no_calhunter = unpack_all_no_calhunter + full_reduction

process_and_stack = (
    second_pass_astrometry
    + second_pass_validate_astrometry_export_and_filter
    + stack_dithers
    + [
        ImageSaver(output_dir_name="stack"),
    ]
)

realtime = extract_all + mask_and_split + save_raw + full_reduction

full = realtime + imsub

candidates = detect_candidates + process_candidates

# Other miscellaneous blocks
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

# Blocks for testing
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

select_for_test_ref = [
    ImageSelector(
        ("FIELDID", str(3944)),
        ("BOARD_ID", str(4)),
    ),
    ImageDebatcher(),
    ImageBatcher("STACKID"),
]

reftest = (
    unpack_subset
    + dark_calibrate
    + first_pass_flat_calibrate
    + process_and_stack
    + select_for_test_ref
    + refbuild
)
