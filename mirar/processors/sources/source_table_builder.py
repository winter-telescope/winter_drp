"""
Module to extract a candidates table from an image header
"""
import pandas as pd

from mirar.data import ImageBatch, SourceBatch, SourceTable
from mirar.data.utils import get_xy_from_wcs
from mirar.errors import ProcessorError
from mirar.paths import CAND_DEC_KEY, CAND_RA_KEY, XPOS_KEY, YPOS_KEY
from mirar.processors.base_processor import BaseSourceGenerator


class TableFromHeaderError(ProcessorError):
    """Error relating to writing a source table from a header"""


class HeaderKeyMissingError(ProcessorError):
    """Error relating to missing keys in headers"""


class ForcedPhotometryDetector(BaseSourceGenerator):
    """
    Class to create a candidates table for performing forced photometry
    """

    base_key = "forcedphot"

    def __init__(
        self,
        calculate_image_coordinates: bool = True,
        ra_header_key: str = CAND_RA_KEY,
        dec_header_key: str = CAND_DEC_KEY,
    ):
        super().__init__()
        self.calculate_image_coordinates = calculate_image_coordinates
        self.ra_header_key = ra_header_key
        self.dec_header_key = dec_header_key

    def _apply_to_images(self, batch: ImageBatch) -> SourceBatch:
        all_cands = SourceBatch()
        for image in batch:
            # Save the image here, to facilitate processing downstream
            header = image.get_header()

            new_dict = {
                self.ra_header_key: image[self.ra_header_key],
                self.dec_header_key: image[self.dec_header_key],
            }

            if self.calculate_image_coordinates:
                x, y = get_xy_from_wcs(
                    ra_deg=image[self.ra_header_key],
                    dec_deg=image[self.dec_header_key],
                    header=header,
                )
                new_dict[XPOS_KEY] = x
                new_dict[YPOS_KEY] = y

            src_table = pd.DataFrame([new_dict])

            print(src_table)

            metadata = self.get_metadata(image)

            all_cands.append(SourceTable(src_table, metadata=metadata))

        return all_cands

    #
    # def append_keys_to_header(self, header: Header):
    #     if UNC_IMG_KEY not in header.keys():
    #         header[UNC_IMG_KEY] = None
    #     if NORM_PSFEX_KEY not in header.keys():
    #         header[NORM_PSFEX_KEY] = None
    #     return header


#
# class SourceTablefromCoordinates(ForcedPhotometryDetector):
#     """
#     Class to create a source table to run forced photometry from user-specified
#     coordinates
#     """
#
#     base_key = "coords_table_exporter"
#
#     def __init__(
#         self,
#         ra_deg: float | list[float],
#         dec_deg: float | list[float],
#         ra_header_key: str = "USERRA",
#         dec_header_key: str = "USERDEC",
#         name_header_key: str = "USERNAME",
#     ):
#         self.ra_deg = ra_deg
#         self.dec_deg = dec_deg
#         super().__init__(
#             ra_header_key=ra_header_key,
#             dec_header_key=dec_header_key,
#             name_header_key=name_header_key,
#         )
#
#     def append_keys_to_header(self, header: Header):
#         header["USERRA"] = self.ra_deg
#         header["USERDEC"] = self.dec_deg
#         if UNC_IMG_KEY not in header.keys():
#             header[UNC_IMG_KEY] = None
#         if NORM_PSFEX_KEY not in header.keys():
#             header[NORM_PSFEX_KEY] = None
#         return header
