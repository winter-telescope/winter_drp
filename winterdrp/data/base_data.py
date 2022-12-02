"""
This contains the base data classes for the :module:`wintedrp.processors`.

The smallest unit is a :class:`~winterdrp.data.image_data.DataBlock` object, corresponding to a single image.
These :class:`~winterdrp.data.image_data.DataBlock` objects are grouped into
:class:`~winterdrp.data.image_data.DataBatch` objects. Each :class:`~wintedrp.processors.BaseProcessor` will
operate on a individual :class:`~winterdrp.data.image_data.DataBatch` object.

The :class:`~winterdrp.data.image_data.DataBatch` objects are stored within a larger
:class:`~winterdrp.data.image_data.DataSet` object.
A :class:`~wintedrp.processors.BaseProcessor` will iterate over each
:class:`~winterdrp.data.image_data.DataBatch` in a :class:`~winterdrp.data.image_data.DataSet`.
"""
import logging
from pathlib import Path
from typing import Type

from winterdrp.paths import base_name_key, raw_img_key

logger = logging.getLogger(__name__)


class DataBlock:
    def __init__(self):
        self.raw_img_list = self[raw_img_key].split(",")
        self.base_name = self[base_name_key]

    def __getitem__(self, item):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def get_name(self) -> str:
        return self.base_name

    def get_raw_img_list(self) -> list[str]:
        return self.raw_img_list


class PseudoList:
    """
    Base Class for a list-like object which contains a list of data.
    Other classes inherit from this object.

    The basic idea is that this class holds all the functions
    for safely creating an object with a specified data type.

    This class also contains the relevant magic functions so that `len(x)`, `x[i] = N`,
    and `for y in x` work as intended.
    """

    @property
    def data_type(self):
        raise NotImplementedError()

    def __init__(self, data_list=None):

        self._datalist = []

        if data_list is None:
            data_list = []
        elif isinstance(data_list, self.data_type):
            data_list = [data_list]

        if not isinstance(data_list, list):
            err = f"Found {data_list} of type {type(data_list)}. Expected a list."
            logger.error(err)
            raise ValueError(err)

        for item in data_list:
            self.append(item)

    def get_data_list(self):
        return self._datalist

    def append(self, item):
        self._append(item)

    def _append(self, item):
        if not isinstance(item, self.data_type):
            err = f"Error appending item {item} of type {type(item)}. Expected a {self.data_type} item"
            logger.error(err)
            raise ValueError(err)

        if len(self._datalist) > 0:
            if not type(self._datalist[0]) == type(item):
                err = (
                    f"Error appending item {item} of type {type(item)}. This {self.__class__.__name__} "
                    f"object already contains data of type {type(self._datalist[0])}. "
                    f"Please ensure all data is of the same type."
                )
                logger.error(err)
                raise ValueError(err)
        self._datalist.append(item)

    def __getitem__(self, item):
        return self._datalist.__getitem__(item)

    def __setitem__(self, key, value):
        self._datalist.__setitem__(key, value)

    def __add__(self, other):
        new = self.__class__()
        for item in self.get_data_list():
            new.append(item)
        for item in other.get_data_list():
            new.append(item)
        return new

    def __iadd__(self, other):
        for item in other.get_data_list():
            self._datalist.append(item)
        return self

    def __len__(self):
        return self._datalist.__len__()

    def __iter__(self):
        return self._datalist.__iter__()


class DataBatch(PseudoList):
    @property
    def data_type(self) -> Type[DataBlock]:
        raise NotImplementedError()

    def __init__(self, batch: list[DataBlock] | DataBlock = None):
        super().__init__(data_list=batch)

    def get_batch(self) -> list[DataBlock]:
        return self.get_data_list()

    def get_raw_image_names(self) -> list[str]:
        img_list = []
        for data_block in self.get_batch():
            img_list += [Path(x).name for x in data_block.get_raw_img_list()]
        return img_list


class Dataset(PseudoList):

    data_type = DataBatch

    def get_batches(self):
        return self.get_data_list()

    def __init__(self, batches: list[DataBatch] | DataBatch = None):
        super().__init__(data_list=batches)
