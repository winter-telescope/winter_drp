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
    "ZP_2.0": 24.05931984677565,
    "ZP_2.0_std": 0.03830265576481768,
    "ZP_2.0_nstars": 114,
    "ZP_3.0": 24.5182462444065,
    "ZP_3.0_std": 0.03897102606054595,
    "ZP_3.0_nstars": 113,
    "ZP_4.0": 24.66877193729583,
    "ZP_4.0_std": 0.04413923966098385,
    "ZP_4.0_nstars": 115,
    "ZP_5.0": 24.735337207194643,
    "ZP_5.0_std": 0.04470635796321621,
    "ZP_5.0_nstars": 115,
    "ZP_6.0": 24.756819402061478,
    "ZP_6.0_std": 0.045164962968125014,
    "ZP_6.0_nstars": 115,
    "ZP_7.0": 24.77976130514258,
    "ZP_7.0_std": 0.04516449922952734,
    "ZP_7.0_nstars": 115,
    "ZP_8.0": 24.791871235399995,
    "ZP_8.0_std": 0.045112750520510565,
    "ZP_8.0_nstars": 115,
    "ZP_AUTO": 24.79282472222403,
    "ZP_AUTO_std": 0.045853218043986683,
    "ZP_AUTO_nstars": 115,
    "ZP_PSF": 24.728054363490656,
    "ZP_PSF_std": 0.037042100713524956,
    "ZP_PSF_nstars": 111,
    "SCORMEAN": -0.08252085765164723,
    "SCORMED": -0.06930644943369992,
    "SCORSTD": 1.2697482555083541,
}
expected_dataframe_values = {
    "magpsf": [
        17.080945751150622,
        14.708106222027595,
        17.022750119829055,
        16.610904782427035,
        17.00821547529815,
        15.083344543039614,
        17.20262789934139,
        16.577858978827802,
        17.158604324326824,
        17.199527444628906,
        17.27594948160655,
        16.439715610781313,
        16.74298394575055,
        16.90284959273128,
        15.361447411583198,
        13.403504301394129,
        15.900416455898991,
        16.671780747005037,
        16.729265975344596,
        17.063889137217537,
        17.330950249758722,
        15.448761709210673,
        16.97604942403651,
        15.974175632636472,
        16.936752852987013,
        17.10199694292421,
        16.94319319035184,
        17.36789780216876,
        16.34422475877286,
        17.032302513390142,
        13.799390633284723,
        16.891713940452558,
        17.38269290373386,
        17.210960145015548,
        17.13774520911883,
        16.89176826811356,
        17.017207170910268,
        16.88725093350201,
        13.03394604219924,
        13.441959283137027,
        16.804435662879868,
        17.172036149770882,
        16.709798485433048,
        17.004112384222225,
        17.3089991836995,
        16.896276973809492,
        17.062648930268136,
        14.165765950329677,
        16.816833387421166,
        17.25798634387369,
        16.472393342354607,
        16.12811580044614,
        16.913044144352817,
        16.268274912394237,
        17.080148820424736,
        13.47613884658073,
        16.425583658844143,
        16.75108946818958,
        16.755069641373844,
        16.717891550554384,
        16.72425486563276,
        16.462018948904134,
        16.926717165375624,
        16.610232516100197,
        16.357849492106514,
        16.6979110423582,
        16.518174380369885,
        16.74647586576681,
        17.007835404136856,
        16.844111593569146,
        16.8340556097207,
        16.732168332845042,
        17.08749231101348,
        17.004516094731088,
        16.939554063633867,
        17.107446123685204,
        16.809913610091975,
        17.162522468430105,
        17.121368200546932,
        16.678845076290756,
        16.83265560516275,
        16.40310284029951,
        16.339574015662656,
        16.103111705333873,
        17.15340493534194,
        16.896123215615198,
        16.40243616039653,
        17.1582931546209,
        16.459604745207848,
        17.19450107263499,
        17.080459984705314,
        15.385225939178683,
        16.752597031290563,
        16.054354498228832,
        16.892133609291236,
        17.21063020807636,
        16.843345213298324,
        17.046073451061847,
        15.083932309155868,
        17.005670537635034,
        16.502765523687053,
        17.233621983138807,
        16.25253991989338,
        16.792475363556207,
        17.166090455912737,
        17.184076767955517,
        14.161989445395921,
        13.915740806363097,
        17.015245779545417,
        17.14100241170922,
        17.02748021543208,
        16.473754038876688,
        16.95371446975483,
        17.25862764580871,
        16.970047144963175,
        16.456309223219534,
        16.795726077554612,
        16.724194652456312,
        17.03003655146124,
        17.371117319852733,
        13.207472235771684,
        16.825596397232204,
        16.921597421752924,
        16.627804357173176,
        17.173908929043368,
        17.289434436432987,
        16.860161926238483,
        16.67987198304645,
        16.350044321461816,
        16.64659657729659,
        16.334020989295787,
        16.955573136373012,
        17.00390944462132,
        16.828263678065163,
        16.730433842348425,
        17.0782404690106,
        17.084119394019353,
        16.73527213591415,
        17.12199043952996,
        17.04345172487818,
        17.3442701053555,
        17.001986744948834,
        16.824830565114077,
        16.94922343991597,
        17.2948269136125,
        17.093191747370042,
        17.273424922851895,
        17.091147256988588,
        16.996458095823126,
        17.35204129179263,
        17.050534676211765,
        14.613900678468525,
        16.980103906679226,
        17.289130974003953,
        17.060689510213372,
        17.105322606609835,
        16.9180294198705,
        14.25804335077192,
        16.925405738907504,
        16.63195525193173,
        17.317228264482818,
        11.977605148619725,
        17.124705534009276,
        14.363627424786785,
        16.61936326494321,
        17.34971534768361,
        17.221842755687632,
        16.797271781138946,
    ],
    "magap": [
        16.87462708006406,
        15.445316092168218,
        16.53502410000455,
        16.872505578594605,
        17.07791801758546,
        14.88310366512772,
        17.3153096998834,
        16.300301355617016,
        17.1890094881321,
        16.50051339289036,
        17.159360313708852,
        16.380488838505187,
        16.334410568585582,
        16.51438903772086,
        15.358232592252131,
        14.048450482049532,
        16.570897952031537,
        16.793064766811668,
        17.318113590735997,
        16.73386038486479,
        17.547275598485243,
        15.7757855441433,
        16.707730511514146,
        15.982020059352218,
        17.245711924928926,
        17.23652169796587,
        16.72344146888542,
        17.76821145174536,
        16.70603401528382,
        16.898418033208824,
        14.305085355801188,
        16.592692192574187,
        16.562477079918963,
        17.00370024133123,
        16.768273751380647,
        16.807450650187107,
        17.044837209854133,
        17.34454075853897,
        12.607325077998224,
        13.753421468091428,
        16.084975225549428,
        17.155416440067505,
        16.76966340041968,
        16.399964540717654,
        17.052680868051894,
        17.511190369031432,
        16.648898897170398,
        14.938491798689634,
        16.811322459458633,
        16.737275407920816,
        16.31536466625427,
        14.562537369131663,
        16.757921934687882,
        16.43328387734389,
        17.00860950270895,
        14.32907965593547,
        15.719589055184226,
        16.908650205915656,
        16.222960638872884,
        16.19975010564343,
        16.445242676622506,
        16.18357700711738,
        16.299595509403517,
        16.95815415066128,
        17.125802924283413,
        16.958943025601723,
        16.059200014423133,
        16.614094217101023,
        16.727398930456772,
        16.30942643739309,
        16.705871095825547,
        16.470904345526833,
        17.519529126546878,
        16.5113519271329,
        16.730837568185592,
        17.012498339203937,
        15.907758916526598,
        17.50880197598907,
        16.60335987759278,
        16.00533195012615,
        16.354004429455426,
        17.21217732663935,
        15.992988052475422,
        15.921949087103531,
        16.573889082751027,
        16.761625157824014,
        16.408863999233052,
        16.399596552246376,
        16.355299069478818,
        16.708587413266166,
        16.31024801018228,
        15.859916551889343,
        16.91703574897814,
        16.19254397136892,
        16.65842608103067,
        16.88602319911652,
        16.20988737341061,
        16.70726583782669,
        13.883652898311016,
        16.544499190350805,
        16.160956699505434,
        16.59905636305212,
        15.949890081823035,
        16.796046606215004,
        17.050682216800272,
        16.585734955892196,
        14.769396110002456,
        14.480123632813251,
        16.498875286185196,
        16.427396551582373,
        16.744876864104157,
        16.565014011158624,
        16.554048235999907,
        16.93145002284904,
        16.77255335482007,
        16.390504179564115,
        16.172484552502212,
        16.232768473465804,
        17.261886796275203,
        16.98391807188197,
        13.682144100490515,
        16.378972887509235,
        17.04749081371895,
        15.996486105294599,
        16.789513548871145,
        16.756020451725817,
        16.40139117021704,
        16.678457727006958,
        16.03690171084004,
        17.218450328647183,
        15.925774039920292,
        16.35826052058541,
        16.435210613410298,
        17.070500194584664,
        16.861410184500308,
        17.295098480954593,
        16.96170662032879,
        15.835611350271234,
        16.22430990615117,
        17.102714614440387,
        16.93607719052254,
        16.323178433521235,
        16.058902571258926,
        16.361095001064143,
        16.601789454000375,
        16.801470476229152,
        16.77792599346344,
        16.924407617510553,
        16.319508525640792,
        17.903056284268583,
        16.665464067147234,
        15.402522385858607,
        16.06738401012889,
        17.24110295649703,
        16.81910696957604,
        17.212357914985,
        16.68381039202975,
        14.958763463401759,
        16.549400052944115,
        15.915883440199979,
        17.04538890974478,
        12.026487156686375,
        17.460936402417772,
        14.972024545250912,
        16.2531987291213,
        16.74351684436303,
        17.435456010551267,
        16.76502361691559,
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

        self.assertEqual(len(candidates_table), 207)
        for key, value in expected_dataframe_values.items():
            if isinstance(value, list):
                for ind, val in enumerate(value):
                    self.assertAlmostEqual(
                        candidates_table.iloc[ind][key], val, delta=0.05
                    )
