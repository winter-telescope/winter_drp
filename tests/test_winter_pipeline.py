"""
Tests for WINTER reduction
"""
import logging
import shutil

from mirar.data import Dataset, ImageBatch
from mirar.paths import get_output_dir
from mirar.pipelines import get_pipeline
from mirar.testing import BaseTestCase

logger = logging.getLogger(__name__)

expected_zp = {
    "ZP_2.0": 24.004793167114258,
    "ZP_2.0_std": 0.046376824378967285,
    "ZP_2.0_nstars": 55,
    "ZP_3.0": 24.535335540771484,
    "ZP_3.0_std": 0.03816154599189758,
    "ZP_3.0_nstars": 51,
    "ZP_4.0": 24.716201782226562,
    "ZP_4.0_std": 0.04618291184306145,
    "ZP_4.0_nstars": 53,
    "ZP_5.0": 24.778196334838867,
    "ZP_5.0_std": 0.04734010249376297,
    "ZP_5.0_nstars": 54,
    "ZP_6.0": 24.82450294494629,
    "ZP_6.0_std": 0.0532773993909359,
    "ZP_6.0_nstars": 57,
    "ZP_7.0": 24.814254760742188,
    "ZP_7.0_std": 0.047826092690229416,
    "ZP_7.0_nstars": 53,
    "ZP_8.0": 24.85060691833496,
    "ZP_8.0_std": 0.055966123938560486,
    "ZP_8.0_nstars": 57,
    "ZP_AUTO": 24.870363235473633,
    "ZP_AUTO_std": 0.04606800898909569,
    "ZP_AUTO_nstars": 53,
    "SCORMEAN": -0.0611156090659958,
    "SCORMED": -0.06021853428525067,
    "SCORSTD": 1.26991899442293,
}
expected_dataframe_values = {
    "magpsf": [
        17.40257635892123,
        17.132789131901372,
        17.15180632086564,
        17.150834006146,
        16.08964475433679,
        16.853751115983446,
        17.344383443534426,
        17.243287079027194,
        16.77763453944769,
        13.797662089072626,
        14.703371506598113,
        17.26207308998179,
        16.89061820794825,
        16.929368627817528,
        15.58800006631549,
        16.845085743601796,
        17.04230820303284,
        14.513855625259932,
        17.220953248107627,
        16.32098943401457,
        17.067441439163346,
        17.176495945046355,
        17.18608279707326,
        16.66254318439492,
        17.287668972426673,
        14.806871213355937,
        16.625094935666024,
        14.011307351591476,
        17.024175753581268,
        17.322509852040263,
        17.12731726154371,
        16.92214945791004,
        17.266879685581603,
        17.189106477583678,
        15.177965575491159,
        16.79257590885456,
        16.46334615513491,
        16.177752561137297,
        14.308998547451987,
        16.94348397592392,
        16.805300503927974,
        16.76710180023848,
        16.736675982211604,
        16.797307497274886,
        16.960732169965766,
        17.131187670182527,
        16.505630981081776,
        17.370879870675157,
        15.8629626486919,
        16.699723602402905,
        16.919792253475066,
        17.176785971024888,
        17.043628819710133,
        16.464664090785874,
        16.85226537084872,
        14.32337785600473,
        17.291303876442335,
        17.160405635725407,
        16.416630003259684,
        16.657708826727053,
        17.346872814640605,
        14.754083185648721,
        17.20758845591862,
        16.46774507846163,
        17.21291283272504,
        17.221761069771485,
        17.0397003055971,
        14.119261566897372,
        17.177993605260326,
        17.20298786605664,
        17.263051484797476,
        17.03456019630027,
        17.413354465598957,
        16.524534144177395,
        16.4554621026546,
        16.42338542411802,
        15.834731126833375,
        15.342339075113161,
        16.533922335088317,
        17.17727999166496,
        16.923802520142736,
        17.31226514888295,
        17.123322291151528,
        17.363160210596934,
        17.006784298409578,
        17.31308456310687,
        17.396157662256172,
        16.740131177992488,
        16.40342307393489,
        17.27340781047485,
        16.859302772511676,
        17.303314099025787,
    ],
    "magap": [
        15.846433190410702,
        18.08705422066798,
        16.840919588109422,
        15.791803935777287,
        15.714748915768363,
        15.258340158473398,
        16.493607418696907,
        16.830713817701575,
        15.616150780241206,
        14.274544802416113,
        14.640098017087885,
        16.270198523719266,
        16.9562311053664,
        17.75748464047038,
        14.4354447214705,
        15.423107088704297,
        15.968638904012408,
        14.21393538458738,
        15.800370112908812,
        15.164272175723799,
        16.212392942390444,
        16.07543764751933,
        15.949529512635282,
        16.163467923041384,
        15.996089023979826,
        14.605929307048152,
        16.18283093725323,
        13.113421889563202,
        16.201267371262368,
        16.13004883733624,
        15.996982000341179,
        16.5582695875922,
        16.09413227621394,
        16.423725084329234,
        14.634597656037851,
        15.514932005145397,
        15.41138363544031,
        14.933282895236749,
        15.15145717671035,
        15.722475118707273,
        16.58629223738939,
        15.657663678623337,
        15.73961341599891,
        15.302131855535334,
        16.329500219184947,
        16.149917137860832,
        17.17144782575151,
        18.203943042630673,
        14.884908529896748,
        15.320213009954205,
        15.659219931120118,
        17.07133987486026,
        16.243678022861626,
        16.42659395721479,
        15.90457608583356,
        14.001821207846756,
        15.872870771744477,
        17.188063713518222,
        15.487774279093566,
        17.229092730835667,
        17.881656213407943,
        14.767809685652265,
        16.079252316193454,
        17.360953531282778,
        15.707545799581306,
        16.695218717127812,
        15.732070962692012,
        14.355740750366271,
        17.033585581291945,
        16.775764191151403,
        17.32322689278215,
        15.981319840518308,
        17.316930063440616,
        16.440978824068786,
        15.039697803114503,
        14.988111300599002,
        16.565207068489244,
        14.282121909402449,
        15.635054132380771,
        16.10711203334788,
        15.98908471192912,
        16.164995055461787,
        15.918783863543041,
        16.95414408948752,
        16.76830742674879,
        17.593109533258552,
        17.91547280652164,
        16.01208707804849,
        14.813839327713515,
        16.246486103800322,
        16.07718730889792,
        16.37301548143858,
    ],
}
pipeline = get_pipeline(
    instrument="winter", selected_configurations=["test"], night="20230726"
)

logging.basicConfig(level=logging.DEBUG)


# @unittest.skip(
#     "WFAU is down"
# )
class TestWinterPipeline(BaseTestCase):
    """
    Module for testing winter pipeline
    """

    def setUp(self):
        """
        Function to set up test
        Returns:

        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def test_pipeline(self):
        """
        Test winter pipeline
        Returns:

        """
        self.logger.info("\n\n Testing winter pipeline \n\n")

        res, _ = pipeline.reduce_images(Dataset([ImageBatch()]), catch_all_errors=False)

        # Cleanup - delete ouptut dir
        output_dir = get_output_dir(dir_root="winter/20230726")
        shutil.rmtree(output_dir)

        # Expect one dataset, for one different sub-boards
        self.assertEqual(len(res[0]), 1)

        source_table = res[0][0]

        # # Uncomment to print new expected ZP dict
        print("New Results WINTER:")
        new_exp = "expected_zp = { \n"
        for header_key in source_table.get_metadata():
            if header_key in expected_zp:
                new_exp += f'    "{header_key}": {source_table[header_key]}, \n'
        new_exp += "}"
        print(new_exp)

        new_candidates_table = source_table.get_data()

        new_exp_dataframe = "expected_dataframe_values = { \n"
        for key in expected_dataframe_values:
            new_exp_dataframe += f'    "{key}": {list(new_candidates_table[key])}, \n'
        new_exp_dataframe += "}"

        print(new_exp_dataframe)

        for key, value in expected_zp.items():
            if isinstance(value, float):
                self.assertAlmostEqual(value, source_table[key], places=2)
            elif isinstance(value, int):
                self.assertEqual(value, source_table[key])
            else:
                raise TypeError(
                    f"Type for value ({type(value)} is neither float not int."
                )

        candidates_table = source_table.get_data()

        self.assertEqual(len(candidates_table), 3)
        for key, value in expected_dataframe_values.items():
            if isinstance(value, list):
                for ind, val in enumerate(value):
                    self.assertAlmostEqual(
                        candidates_table.iloc[ind][key], val, delta=0.05
                    )
