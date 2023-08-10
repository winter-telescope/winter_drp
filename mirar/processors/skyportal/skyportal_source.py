"""
Module for sending candidates to Fritz.
"""
import base64
import gzip
import io
import logging
import time
from copy import deepcopy
from typing import Mapping, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.visualization import (
    AsymmetricPercentileInterval,
    ImageNormalize,
    LinearStretch,
    LogStretch,
)

from mirar.data import SourceBatch, SourceTable
from mirar.paths import CAND_NAME_KEY, PACKAGE_NAME, __version__
from mirar.processors.base_processor import BaseSourceProcessor
from mirar.processors.skyportal.client import SkyportalClient

matplotlib.use("agg")

logger = logging.getLogger(__name__)


class SkyportalUploadPhotometry(BaseSourceProcessor):
    """
    Processor for sending source photometry to Skyportal.
    """

    base_key = "skyportalsender"

    def __init__(
        self,
        origin: str,
        group_ids: list[int],
        fritz_filter_id: int,
        instrument_id: int,
        stream_id: int,
        update_thumbnails: bool = True,
    ):
        super().__init__()
        self.group_ids = group_ids
        self.fritz_filter_id = fritz_filter_id
        self.instrument_id = instrument_id
        self.origin = origin  # used for sending updates to Fritz
        self.stream_id = stream_id
        self.update_thumbnails = update_thumbnails
        self.skyportal_client = SkyportalClient()

    def _apply_to_sources(
        self,
        batch: SourceBatch,
    ) -> SourceBatch:
        """
        Apply the processor to a batch of candidates.

        :param batch: SourceBatch to process
        :return: SourceBatch after processing
        """
        for source_table in batch:
            self.export_source_to_skyportal(source_table)
        return batch

    @staticmethod
    def read_input_df(candidate_df: pd.DataFrame):
        """Takes a DataFrame, which has multiple candidate
        and creates list of dictionaries, each dictionary
        representing a single candidate.

        Args:
            candidate_df (pandas.core.frame.DataFrame): dataframe of all candidates.

        Returns:
            (list[dict]): list of dictionaries, each a candidate.
        """
        all_candidates = []

        for i in range(0, len(candidate_df)):
            candidate = {}
            for key in candidate_df.keys():
                try:
                    if isinstance(candidate_df.iloc[i].get(key), (list, str)):
                        candidate[key] = candidate_df.iloc[i].get(key)
                    else:
                        # change to native python type
                        candidate[key] = candidate_df.iloc[i].get(key).item()
                except AttributeError:  # for IOBytes objs
                    candidate[key] = candidate_df.iloc[i].get(key)

            all_candidates.append(candidate)

        return all_candidates

    def skyportal_post_source(self, alert: dict, group_ids: Optional[list[int]] = None):
        """Add a new source to SkyPortal

        :param alert: dict of source info
        :param group_ids: list of group_ids to post source to, defaults to None
        :return: None
        """
        if group_ids is None:
            group_ids = self.group_ids

        data = {
            "ra": alert["ra"],
            "dec": alert["dec"],
            "id": alert[CAND_NAME_KEY],
            "group_ids": group_ids,
            "origin": self.origin,
        }

        logger.debug(
            f"Saving {alert[CAND_NAME_KEY]} {alert['candid']} as a Source on SkyPortal"
        )
        response = self.api("POST", "sources", data)

        if response.json()["status"] == "success":
            logger.debug(
                f"Saved {alert[CAND_NAME_KEY]} {alert['candid']} "
                f"as a Source on SkyPortal"
            )
        else:
            err = (
                f"Failed to save {alert[CAND_NAME_KEY]} {alert['candid']} "
                f"as a Source on SkyPortal"
            )
            logger.error(err)
            logger.error(response.json())

    def api(
        self, method: str, endpoint: str, data: Optional[Mapping] = None
    ) -> requests.Response:
        """Make an API call to a SkyPortal instance

        headers = {'Authorization': f'token {self.token}'}
        response = requests.request(method, endpoint, json_dict=data, headers=headers)

        :param method: HTTP method
        :param endpoint: API endpoint e.g sources
        :param data: JSON data to send
        :return: response from API call
        """
        return self.skyportal_client.api(method, endpoint, data)

    def make_thumbnail(self, alert, skyportal_type: str, alert_packet_type: str):
        """
        Convert lossless FITS cutouts from ZTF-like alerts into PNGs.
        Make thumbnail for pushing to SkyPortal.

        :param alert: ZTF-like alert packet/dict
        :param skyportal_type: <new|ref|sub> thumbnail type expected by SkyPortal
        :param alert_packet_type: <Science|Template|Difference> survey naming
        :return:
        """
        alert = deepcopy(alert)
        cutout_data = alert[f"cutout{alert_packet_type}"]

        with gzip.open(io.BytesIO(cutout_data), "rb") as cutout:
            with fits.open(
                io.BytesIO(cutout.read()), ignore_missing_simple=True
            ) as hdu:
                image_data = hdu[0].data  # pylint: disable=no-member

        buff = io.BytesIO()
        plt.close("all")
        fig = plt.figure()
        fig.set_size_inches(4, 4, forward=False)
        ax_1 = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
        ax_1.set_axis_off()
        fig.add_axes(ax_1)

        # replace nans with median:
        img = np.array(image_data)
        # replace dubiously large values
        xl_mask = np.greater(np.abs(img), 1e20, where=~np.isnan(img))
        if img[xl_mask].any():
            img[xl_mask] = np.nan
        if np.isnan(img).any():
            median = float(np.nanmean(img.flatten()))
            img = np.nan_to_num(img, nan=median)

        norm = ImageNormalize(
            img,
            stretch=LinearStretch()
            if alert_packet_type == "Difference"
            else LogStretch(),
        )
        img_norm = norm(img)
        normalizer = AsymmetricPercentileInterval(
            lower_percentile=1, upper_percentile=100
        )
        vmin, vmax = normalizer.get_limits(img_norm)
        ax_1.imshow(img_norm, cmap="bone", origin="lower", vmin=vmin, vmax=vmax)
        plt.savefig(buff, dpi=42)

        buff.seek(0)
        plt.close("all")

        thumbnail_dict = {
            "obj_id": alert[CAND_NAME_KEY],
            "data": base64.b64encode(buff.read()).decode("utf-8"),
            "ttype": skyportal_type,
        }

        return thumbnail_dict

    def skyportal_post_thumbnails(self, alert):
        """Post alert Science, Reference, and Subtraction thumbnails to SkyPortal

        :param alert: dict of source/candidate information
        :return:
        """
        for ttype, instrument_type in [
            ("new", "Science"),
            ("ref", "Template"),
            ("sub", "Difference"),
        ]:
            logger.debug(
                f"Making {instrument_type} thumbnail for {alert[CAND_NAME_KEY]} "
                f"{alert['candid']}",
            )
            thumb = self.make_thumbnail(alert, ttype, instrument_type)

            logger.debug(
                f"Posting {instrument_type} thumbnail for {alert[CAND_NAME_KEY]} "
                f"{alert['candid']} to SkyPortal",
            )
            response = self.api("POST", "thumbnail", thumb)

            if response.json()["status"] == "success":
                logger.debug(
                    f"Posted {alert[CAND_NAME_KEY]} {alert['candid']} "
                    f"{instrument_type} cutout to SkyPortal"
                )
            else:
                logger.error(
                    f"Failed to post {alert[CAND_NAME_KEY]} {alert['candid']} "
                    f"{instrument_type} cutout to SkyPortal"
                )
                logger.error(response.json())

    def make_photometry(self, alert, jd_start: Optional[float] = None):
        """
        Make a de-duplicated pandas.DataFrame with photometry of alert[CAND_NAME_KEY]
        Modified from Kowalksi (https://github.com/dmitryduev/kowalski)

        :param alert: candidate dictionary
        :param jd_start: date from which to start photometry from
        """
        alert = deepcopy(alert)
        top_level = [
            "schemavsn",
            "publisher",
            CAND_NAME_KEY,
            "candid",
            "candidate",
            "prv_candidates",
            "cutoutScience",
            "cutoutTemplate",
            "cutoutDifference",
        ]
        alert["candidate"] = {}

        # (keys having value in 3.)
        delete = [key for key in alert.keys() if key not in top_level]

        # delete the key/s
        for key in delete:
            alert["candidate"][key] = alert[key]
            del alert[key]

        alert["candidate"] = [alert["candidate"]]
        df_candidate = pd.DataFrame(alert["candidate"], index=[0])

        df_prv_candidates = pd.DataFrame(alert["prv_candidates"])

        df_light_curve = pd.concat(
            [df_candidate, df_prv_candidates], ignore_index=True, sort=False
        )

        # note: WNTR (like PGIR) uses 2massj, which is not in sncosmo as of
        # 20210803, cspjs seems to be close/good enough as an approximation
        df_light_curve["filter"] = "cspjs"  # FIXME

        df_light_curve["magsys"] = "ab"  # FIXME
        df_light_curve["mjd"] = df_light_curve["jd"] - 2400000.5

        df_light_curve["mjd"] = df_light_curve["mjd"].astype(np.float64)
        df_light_curve["magpsf"] = df_light_curve["magpsf"].astype(np.float32)
        df_light_curve["sigmapsf"] = df_light_curve["sigmapsf"].astype(np.float32)

        df_light_curve = (
            df_light_curve.drop_duplicates(subset=["mjd", "magpsf"])
            .reset_index(drop=True)
            .sort_values(by=["mjd"])
        )

        # filter out bad data:
        mask_good_diffmaglim = df_light_curve["diffmaglim"] > 0
        df_light_curve = df_light_curve.loc[mask_good_diffmaglim]

        # convert from mag to flux

        # step 1: calculate the coefficient that determines whether the
        # flux should be negative or positive
        coeff = df_light_curve["isdiffpos"].apply(
            lambda x: 1.0 if x in [True, 1, "y", "Y", "t", "1"] else -1.0
        )

        # step 2: calculate the flux normalized to an arbitrary AB zeropoint of
        # 23.9 (results in flux in uJy)
        df_light_curve["flux"] = coeff * 10 ** (
            -0.4 * (df_light_curve["magpsf"] - 23.9)
        )

        # step 3: separate detections from non detections
        detected = np.isfinite(df_light_curve["magpsf"])
        undetected = ~detected

        # step 4: calculate the flux error
        df_light_curve["fluxerr"] = None  # initialize the column

        # step 4a: calculate fluxerr for detections using sigmapsf
        df_light_curve.loc[detected, "fluxerr"] = np.abs(
            df_light_curve.loc[detected, "sigmapsf"]
            * df_light_curve.loc[detected, "flux"]
            * np.log(10)
            / 2.5
        )

        # step 4b: calculate fluxerr for non detections using diffmaglim
        df_light_curve.loc[undetected, "fluxerr"] = (
            10 ** (-0.4 * (df_light_curve.loc[undetected, "diffmaglim"] - 23.9)) / 5.0
        )  # as diffmaglim is the 5-sigma depth

        # step 5: set the zeropoint and magnitude system
        df_light_curve["zp"] = 23.9  # FIXME
        df_light_curve["zpsys"] = "ab"  # FIXME

        # only "new" photometry requested?
        if jd_start is not None:
            w_after_jd = df_light_curve["jd"] > jd_start
            df_light_curve = df_light_curve.loc[w_after_jd]

        return df_light_curve

    def skyportal_put_photometry(self, alert):
        """Send photometry to Fritz."""
        logger.debug(
            f"Making alert photometry of {alert[CAND_NAME_KEY]} {alert['candid']}"
        )
        df_photometry = self.make_photometry(alert)

        # post photometry
        photometry = {
            "obj_id": alert[CAND_NAME_KEY],
            "stream_ids": [int(self.stream_id)],
            "instrument_id": self.instrument_id,
            "mjd": df_photometry["mjd"].tolist(),
            "flux": df_photometry["flux"].tolist(),
            "fluxerr": df_photometry["fluxerr"].tolist(),
            "zp": df_photometry["zp"].tolist(),
            "magsys": df_photometry["zpsys"].tolist(),
            "filter": df_photometry["filter"].tolist(),
            "ra": df_photometry["ra"].tolist(),
            "dec": df_photometry["dec"].tolist(),
        }

        if (len(photometry.get("flux", ())) > 0) or (
            len(photometry.get("fluxerr", ())) > 0
        ):
            logger.debug(
                f"Posting photometry of {alert[CAND_NAME_KEY]} {alert['candid']}, "
                f"stream_id={self.stream_id} to SkyPortal"
            )
            response = self.api("PUT", "photometry", photometry)
            if response.json()["status"] == "success":
                logger.debug(
                    f"Posted {alert[CAND_NAME_KEY]} photometry stream_id={self.stream_id} "
                    f"to SkyPortal"
                )
            else:
                logger.error(
                    f"Failed to post {alert[CAND_NAME_KEY]} photometry "
                    f"stream_id={self.stream_id} to SkyPortal"
                )
                logger.error(response.json())

    def skyportal_source_exporter(self, alert):
        """
        Posts a source to SkyPortal.

        :param alert: _description_
        :type alert: _type_
        """
        # check if source exists in SkyPortal
        logger.debug(f"Checking if {alert[CAND_NAME_KEY]} is source in SkyPortal")
        response = self.api("HEAD", f"sources/{alert[CAND_NAME_KEY]}")

        if response.status_code not in [200, 404]:
            response.raise_for_status()

        is_source = response.status_code == 200
        logger.debug(
            f"{alert[CAND_NAME_KEY]} "
            f"{'is' if is_source else 'is not'} source in SkyPortal"
        )

        if not is_source:
            self.skyportal_post_source(alert, group_ids=self.group_ids)
            # post thumbnails
            self.skyportal_post_thumbnails(alert)

        # post full light curve
        self.skyportal_put_photometry(alert)

        if self.update_thumbnails:  # FIXME: ask michael
            self.skyportal_post_thumbnails(alert)

        logger.debug(f"SendToSkyportal Manager complete for {alert[CAND_NAME_KEY]}")

    def export_source_to_skyportal(self, source_table: SourceTable):
        """
        Function to export individual sources as candidates in SkyPortal

        :param source_table: Table containing the data to be processed
        :return: None
        """
        candidate_df = source_table.get_data()
        t_0 = time.time()
        all_cands = self.read_input_df(candidate_df)
        num_cands = len(all_cands)

        for cand in all_cands:
            self.skyportal_source_exporter(cand)

        t_1 = time.time()
        logger.debug(
            f"Took {(t_1 - t_0):.2f} seconds to Skyportal process {num_cands} candidates."
        )
