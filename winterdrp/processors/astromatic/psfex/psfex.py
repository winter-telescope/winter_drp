import logging
import os

import numpy as np
from astropy.io import fits

from winterdrp.data import ImageBatch
from winterdrp.paths import (
    get_output_dir,
    norm_psfex_header_key,
    psfex_header_key,
    sextractor_header_key,
)
from winterdrp.processors.astromatic.sextractor.sextractor import Sextractor
from winterdrp.processors.base_processor import BaseImageProcessor
from winterdrp.utils import execute

logger = logging.getLogger(__name__)


def run_psfex(
    sextractor_cat_path: str,
    config_path: str,
    psf_output_dir: str,
    norm_psf_output_name: str = None,
):
    psfex_command = (
        f"psfex -c {config_path} {sextractor_cat_path} "
        f"-PSF_DIR {psf_output_dir} -CHECKIMAGE_TYPE NONE"
    )

    execute(psfex_command)

    if norm_psf_output_name is not None:
        psf_path = sextractor_cat_path.replace(".cat", ".psf")
        with fits.open(psf_path) as data_file:
            psf_model_data = data_file[1].data[0][0][0]
        psf_model_data = psf_model_data / np.sum(psf_model_data)
        psf_model_hdu = fits.PrimaryHDU(psf_model_data)
        psf_model_hdu.writeto(norm_psf_output_name, overwrite=True)


class PSFex(BaseImageProcessor):
    base_key = "psfex"

    def __init__(
        self,
        config_path: str = None,
        output_sub_dir: str = "psf",
        norm_fits: bool = True,
    ):
        super().__init__()
        self.config_path = config_path
        self.output_sub_dir = output_sub_dir
        self.norm_fits = norm_fits

    def __str__(self) -> str:
        return (
            f"Processor to apply PSFEx to images, measuring the PSF of detected "
            f"sources and saving these to the '{self.output_sub_dir}' directory."
        )

    def get_psfex_output_dir(self):
        return get_output_dir(self.output_sub_dir, self.night_sub_dir)

    def _apply_to_images(self, batch: ImageBatch) -> ImageBatch:
        psfex_out_dir = self.get_psfex_output_dir()

        try:
            os.makedirs(psfex_out_dir)
        except OSError:
            pass

        for image in batch:
            sextractor_cat_path = image[sextractor_header_key]

            psf_path = sextractor_cat_path.replace(".cat", ".psf")
            norm_psf_path = sextractor_cat_path.replace(".cat", ".psfmodel")
            run_psfex(
                sextractor_cat_path=sextractor_cat_path,
                config_path=self.config_path,
                psf_output_dir=os.path.dirname(sextractor_cat_path),
                norm_psf_output_name=norm_psf_path,
            )

            image[psfex_header_key] = psf_path
            image[norm_psfex_header_key] = norm_psf_path
        return batch

    def check_prerequisites(
        self,
    ):
        check = np.sum([isinstance(x, Sextractor) for x in self.preceding_steps])
        if check < 1:
            err = (
                f"{self.__module__} requires {Sextractor} as a prerequisite. "
                f"However, the following steps were found: {self.preceding_steps}."
            )
            logger.error(err)
            raise ValueError
