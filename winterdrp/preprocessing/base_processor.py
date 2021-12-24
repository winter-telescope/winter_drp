import logging
import astropy.io.fits
import numpy as np
import pandas as pd
from winterdrp.io import create_fits

logger = logging.getLogger(__name__)


class BaseProcessor:

    base_name = None
    base_key = None
    requires = []

    subclasses = {}

    def __init__(
            self,
            instrument_vars: dict,
            *args,
            **kwargs
    ):
        self.cache = dict()
        self.open_fits = instrument_vars["open_fits"]

        # Check Processor has a key

        if self.base_key is None:
            err = f"No Base key has been defined for {self.__module__}"
            logger.error(err)
            raise AttributeError(err)

        # Check processor prerequisites are satisfied

        steps = [x[0] for x in instrument_vars["image_steps"]]

        preceding_steps = steps[:steps.index(self.base_key)]

        for x in self.requires:
            if x not in preceding_steps:
                err = f"Processor {self.base_key} requires '{x}' as a prerequisite." \
                      f"However, the pipeline includes {instrument_vars['image_steps']} with " \
                      f"{preceding_steps} occuring before {self.base_key}."
                logger.error(err)
                raise ValueError(err)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses[cls.base_key] = cls

    def _apply_to_images(
            self,
            images: list,
            headers: list,
            sub_dir: str = ""
    ) -> (list, list):
        raise NotImplementedError

    def _update_headers(
            self,
            headers: list,
    ) -> list:
        for header in headers:
            header["CALSTEPS"] += self.base_key
        return headers

    def apply(
            self,
            images: list,
            headers: list,
            sub_dir: str = ""
    ) -> (list, list):
        images, headers = self._apply_to_images(images, headers, sub_dir=sub_dir)
        headers = self._update_headers(headers)
        return images, headers

    @staticmethod
    def get_file_path(header, sub_dir=""):
        raise NotImplementedError

    def load_cache_file(
            self,
            path: str
    ) -> (np.ndarray, astropy.io.fits.Header):

        if path in self.cache:
            img, header = self.cache[path]
        else:
            img, header = self.open_fits(path)
            self.cache[path] = (img, header)
        return img, header

    def select_cache_images(
            self,
            observing_log: pd.DataFrame
    ) -> list:
        mask = observing_log["OBJECT"] == self.base_key
        return observing_log[mask]["RAWIMAGEPATH"]

    def make_cache_files(
            self,
            image_list: list,
            preceding_steps: list,
            sub_dir: str = "",
            *args,
            **kwargs
    ):
        pass

    def save_fits(self, data, header, path):
        self.cache[path] = (data, header)
        logger.info(f"Saving to {path}")
        img = create_fits(data, header=header)
        img.writeto(path, overwrite=True)
