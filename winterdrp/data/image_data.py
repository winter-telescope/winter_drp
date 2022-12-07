"""
Module to specify the input data classes for
:class:`winterdrp.processors.base_processor.ImageHandler`

The basic idea of the code is to pass
:class:`~winterdrp.data.base_data.DataBlock` objects
through a series of :class:`~wintedrp.processors.BaseProcessor` objects.
Since a given image can easily be ~10-100Mb, and there may be several hundred raw images
from a typical survey in a given night, the total data volume for these processors
could be several 10s of Gb or more. Storing these all in RAM would be very
inefficient/slow for a typical laptop or many larger processing machines.

To mitigate this, the code can be operated in **cache mode**. In that case,
after raw images are loaded, only the header data is stored in memory.
The actual image data itself is stored temporarily in as a npy file
in a dedicated cache directory, and only loaded into memory when needed.
When the data is updated, the npy file is changed.
The path of the file is a unique hash, and includes the read time of the file,
so multiple copies of an image can be read and modified independently.

In cache mode, all of the image data is temporarily stored in a cache,
and this cache can therefore reach the size of 10s of Gb.
The location of the cache is in the configurable
**output data directory**. This would increase linearly with successive code executions.
To mitigate that, and to avoid cleaning the cache by hand,
the code tries to automatically delete cache files as needed.

Python provides a default `__del__()` method for handling clean up when an object
is deleted. Images automatically delete their cache in this method. However, has a
somewhat-complicated method of 'garbage collection' (see
`the official description <https://devguide.python.org/internals/garbage-collector>`_
for more info), and it is not guaranteed that Image objects will
clean themselves.

As a fallback, we provide the helper function to delete all cache files created
during a session. When you run the code from the command line (and therefore call
__main__), we automatically run the cleanup before exiting,
even if the code crashes/raises errors. This is also true for the unit tests,
as provided by the  base test class. **If you try to interact with the code in
any other way, please be mindful of this behaviour, and ensure that you clean your
cache in a responsible way!**

If you don't like this feature, you don't need to use it. Cache mode is entirely
optional, and can be disabled by setting the environment variable to false.

.. literalinclude:: ../../winterdrp/paths.py
    :lines: 29

You can change this via an environment variable.

.. code-block:: bash

    export USE_WINTER_CACHE = false

See :doc:`usage` for more information about selecting cache mode,
and setting the output data directory.
"""
import hashlib
import logging

import numpy as np
from astropy.io.fits import Header
from astropy.time import Time

from winterdrp.data.base_data import DataBatch, DataBlock
from winterdrp.paths import CACHE_DIR, USE_CACHE

logger = logging.getLogger(__name__)


class Image(DataBlock):
    """
    A subclass of :class:`~winterdrp.data.base_data.DataBlock`,
    containing an image and header.

    This class serves as input for
    :class:`~winterdrp.processors.base_processor.BaseImageProcessor` and
    :class:`~winterdrp.processors.base_processor.BaseCandidateGenerator` processors.
    """

    cache_files = []

    def __init__(self, data: np.ndarray, header: Header):
        self._data = None
        self.header = header
        super().__init__()
        self.cache_path = self.get_cache_path()
        self.cache_files.append(self.cache_path)
        self.set_data(data)

    def get_cache_path(self):
        base = "".join([str(Time.now()), self.get_name()])
        name = f"{hashlib.sha1(base.encode()).hexdigest()}.npy"
        # cache_dir = get_cache_dir()
        # if not cache_dir.exists():
        #     cache_dir.mkdir(parents=True)
        return CACHE_DIR.joinpath(name)

    def __str__(self):
        return f"<An {self.__class__.__name__} object, built from {self.get_name()}>"

    def get_data(self) -> np.ndarray:
        """
        Get the image data

        :return: image data (numpy array)
        """
        # return self._data
        return np.load(self.cache_path.as_posix())

    def set_data(self, data: np.ndarray):
        """
        Set the data

        :param data: Updated image data
        :return: None
        """
        # self._data = data
        np.save(self.cache_path.as_posix(), data)

    def get_header(self) -> Header:
        """
        Get the image header

        :return: astropy Header
        """
        return self.header

    def set_header(self, header: Header):
        """
        Update the header

        :param header: updated header
        :return: None
        """
        self.header = header

    def __getitem__(self, item):
        return self.header.__getitem__(item)

    def __setitem__(self, key, value):
        self.header.__setitem__(key, value)

    def keys(self):
        """
        Get the header keys

        :return: Keys of header
        """
        return self.header.keys()

    def __del__(self):
        self.cache_path.unlink(missing_ok=True)
        self.cache_files.remove(self.cache_path)


class ImageBatch(DataBatch):
    """
    A subclass of :class:`~winterdrp.data.base_data.DataBatch`,
    which contains :class:`~winterdrp.data.image_data.Image` objects
    """

    data_type = Image

    def __init__(self, batch: list[Image] | Image = None):
        super().__init__(batch=batch)
        # self.cache_list = []

    def append(self, item: Image):
        self._append(item)
        # self.cache_list.append(item.cache_path)

    def __str__(self):
        return (
            f"<An {self.__class__.__name__} object, "
            f"containing {[x.get_name() for x in self.get_batch()]}>"
        )

    def get_batch(self) -> list[Image]:
        """Returns the :class:`~winterdrp.data.image_data.ImageBatch`
        items within the batch

        :return: list of :class:`~winterdrp.data.image_data.Image` objects
        """
        return self.get_data_list()


def clean_cache():
    """Function to clear all created cache files

    :return: None
    """
    # [x.unlink() for x in Image.cache_files]
    for x in Image.cache_files:
        x.unlink()
    Image.cache_files = []
