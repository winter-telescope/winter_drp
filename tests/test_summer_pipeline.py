"""
Tests for summer reduction
"""
import logging

from mirar.data import Dataset, ImageBatch
from mirar.pipelines import get_pipeline
from mirar.testing import BaseTestCase

logger = logging.getLogger(__name__)

expected_zp = {
    "ZP_2.0": 24.381928623072312,
    "ZP_2.0_std": 0.07411375892136553,
    "ZP_2.0_nstars": 30,
    "ZP_3.0": 25.068095736058556,
    "ZP_3.0_std": 0.06619246455805643,
    "ZP_3.0_nstars": 30,
    "ZP_4.0": 25.450715609741213,
    "ZP_4.0_std": 0.06167072958946283,
    "ZP_4.0_nstars": 30,
    "ZP_5.0": 25.662145777893066,
    "ZP_5.0_std": 0.06311382293191249,
    "ZP_5.0_nstars": 30,
    "ZP_6.0": 25.78168761367798,
    "ZP_6.0_std": 0.06425672050707072,
    "ZP_6.0_nstars": 30,
    "ZP_7.0": 25.853945323181154,
    "ZP_7.0_std": 0.06348820708394719,
    "ZP_7.0_nstars": 30,
    "ZP_8.0": 25.902120085906983,
    "ZP_8.0_std": 0.06454072576111243,
    "ZP_8.0_nstars": 30,
    "ZP_AUTO": 25.967076989364624,
    "ZP_AUTO_std": 0.07188784589229257,
    "ZP_AUTO_nstars": 30,
}

pipeline = get_pipeline(
    instrument="summer", selected_configurations=["test"], night="20220402"
)


class TestSummerPipeline(BaseTestCase):
    """
    Module for testing summer pipeline
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
        Test summer pipeline
        Returns:

        """
        self.logger.info("\n\n Testing summer pipeline \n\n")

        res, _ = pipeline.reduce_images(Dataset([ImageBatch()]), catch_all_errors=False)

        self.assertEqual(len(res[0]), 1)

        header = res[0][0].get_header()

        for key, value in expected_zp.items():
            if isinstance(value, float):
                self.assertAlmostEqual(value, header[key], places=2)
            elif isinstance(value, int):
                self.assertEqual(value, header[key])
            else:
                raise TypeError(
                    f"Type for value ({type(value)} is neither float not int."
                )


if __name__ == "__main__":
    print("Calculating latest ZP dictionary")

    new_res, new_errorstack = pipeline.reduce_images(
        dataset=Dataset(ImageBatch()), catch_all_errors=False
    )

    new_header = new_res[0][0].get_header()

    new_exp = "expected_zp = { \n"
    for header_key in new_header.keys():
        if "ZP_" in header_key:
            new_exp += f'    "{header_key}": {new_header[header_key]}, \n'
    new_exp += "}"
    print(new_exp)
