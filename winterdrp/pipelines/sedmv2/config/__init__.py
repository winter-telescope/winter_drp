import os
from winterdrp.pipelines.sedmv2.config.schema import get_sedmv2_schema_path
from winterdrp.processors.utils.cal_hunter import CalRequirement

from winterdrp.pipelines.sedmv2.config.constants import PIPELINE_NAME, SEDMV2_GAIN, SEDMV2_PIXEL_SCALE, DB_NAME

sedmv2_dir = os.path.dirname(__file__)

astromatic_config_dir = os.path.join(sedmv2_dir, 'files')
sedmv2_mask_path = os.path.join(sedmv2_dir, "mask.fits")
sedmv2_weight_path = os.path.join(sedmv2_dir, "weight.fits")

sextractor_astrometry_config = {
    "config_path": os.path.join(astromatic_config_dir, 'astrom.sex'),
    "filter_path": os.path.join(astromatic_config_dir, 'default.conv'),
    "parameter_path": os.path.join(astromatic_config_dir, 'astrom.param'),
    "starnnw_path": os.path.join(astromatic_config_dir, 'default.nnw')
}


sextractor_photometry_config = {
    "config_path": os.path.join(astromatic_config_dir, 'photomCat.sex'),
    "filter_path": os.path.join(astromatic_config_dir, 'default.conv'),
    "parameter_path": os.path.join(astromatic_config_dir, 'photom.param'),
    "starnnw_path": os.path.join(astromatic_config_dir, 'default.nnw')
}

sextractor_candidates_config = {
    "cand_det_sextractor_config": os.path.join(astromatic_config_dir, 'photomCat.sex'),
    "cand_det_sextractor_nnw": os.path.join(astromatic_config_dir, 'default.nnw'),
    "cand_det_sextractor_filter": os.path.join(astromatic_config_dir, 'default.conv'),
    "cand_det_sextractor_params": os.path.join(astromatic_config_dir, 'Scorr.param')
}

scamp_path = os.path.join(astromatic_config_dir, "scamp.conf")

swarp_config_path = os.path.join(astromatic_config_dir, "config.swarp")

psfex_config_path = os.path.join(astromatic_config_dir, "photom.psfex")

sedmv2_cal_requirements = [
    CalRequirement(target_name="bias", required_field="EXPTIME", required_values=["0.0"]),
    CalRequirement(target_name="flat", required_field="FILTERID", required_values=["u", "g", "r", "i"]),
]
