import logging
from pathlib import Path

import astropy
import numpy as np
from astropy.time import Time

from mirar.data import Image
from mirar.io import open_fits, open_raw_image
from mirar.paths import (
    COADD_KEY,
    GAIN_KEY,
    OBSCLASS_KEY,
    PROC_FAIL_KEY,
    PROC_HISTORY_KEY,
    TARGET_KEY,
)

logger = logging.getLogger(__name__)


def load_raw_nires_fits(path: str | Path) -> tuple[np.array, astropy.io.fits.Header]:
    """
    Function to load a raw NIRES image

    :param path: path of file
    :return: data and header of image
    """
    data, header = open_fits(path)
    if GAIN_KEY not in header.keys():
        header[GAIN_KEY] = 1.0
    header["FILTER"] = "ks"

    # header[SNCOSMO_KEY] = sncosmo_filters[header["FILTER"].lower()]

    if "COADDS" in header.keys():
        header["DETCOADD"] = header["COADDS"]

    if header["OBJECT"] in ["acquisition", "pointing", "focus", "none"]:
        header[OBSCLASS_KEY] = header["OBJECT"]
    else:
        header[OBSCLASS_KEY] = "science"

    header["EXPTIME"] = header["ITIME"] * header["DETCOADD"]
    # Apparently for GIT, the images come tagged correctly.
    header[TARGET_KEY] = header["OBJECT"].lower()
    # header["DATE-OBS"] = header["UTSHUT"]
    header["MJD-OBS"] = Time(header["DATE-OBS"]).mjd

    # header.remove("CRVAL1")
    # header.remove("CRVAL2")
    # header.remove("CRPIX1")
    # header.remove("CRPIX2")
    # header.remove("CTYPE1")
    # header.remove("CTYPE2")
    # header.remove("CD1_1")
    # header.remove("CD1_2")
    # header.remove("CD2_1")
    # header.remove("CD2_2")
    header["JD"] = Time(header["DATE-OBS"]).jd

    if COADD_KEY not in header.keys():
        logger.debug(f"No {COADD_KEY} entry. Setting coadds to 1.")
        header[COADD_KEY] = 1

    header[PROC_HISTORY_KEY] = ""
    header[PROC_FAIL_KEY] = ""

    if "FILTERID" not in header.keys():
        header["FILTERID"] = header["FILTER"]

    header["FID"] = header["FILTERID"]

    if "FIELDID" not in header.keys():
        header["FIELDID"] = 99999
    if "PROGPI" not in header.keys():
        header["PROGPI"] = "Kasliwal"
    if "PROGID" not in header.keys():
        header["PROGID"] = 0

    # if "v240419_0034.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240408a"
    # if "v240419_0035.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240408a"
    # if "v240419_0036.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240408a"
    # if "v240419_0037.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240408a"
    # if "v240419_0046.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0047.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0048.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0049.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0053.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0054.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0055.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0056.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0057.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240414a"
    # if "v240419_0064.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240413a"
    # if "v240419_0065.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240413a"
    # if "v240419_0066.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240413a"
    # if "v240419_0067.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240413a"
    # if "v240419_0068.fits" in path.as_posix():
    #     header[TARGET_KEY] = "EP240413a"
    # if "v240419_0082.fits" in path.as_posix():
    #     header[TARGET_KEY] = "GRB240418A"
    # if "v240419_0083.fits" in path.as_posix():
    #     header[TARGET_KEY] = "GRB240418A"
    # if "v240419_0084.fits" in path.as_posix():
    #     header[TARGET_KEY] = "GRB240418A"
    # if "v240419_0085.fits" in path.as_posix():
    #     header[TARGET_KEY] = "GRB240418A"
    # if "v240419_0086.fits" in path.as_posix():
    #     header[TARGET_KEY] = "GRB240418A"

    data = data.astype(float)

    data[980:, :] = np.nan
    data[650:, :80] = np.nan
    return data, header


def load_raw_nires_image(path: str | Path) -> Image:
    """
    Function to load a raw GIT image

    :param path: Path to the raw image
    :return: Image object
    """
    return open_raw_image(path, load_raw_nires_fits)
