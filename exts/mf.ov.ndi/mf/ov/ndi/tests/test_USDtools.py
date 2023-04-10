import omni.kit.test
import omni.kit.ui_test as ui_test
import mf.ov.ndi as ext


class USDUnitTest(omni.kit.test.AsyncTestCase):
    def setUpClass():
        pass

    def tearDownClass():
        pass

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_name_valid(self):
        self.check_name_valid("myDynamicMaterial", "myDynamicMaterial")
        self.check_name_valid("789testing123numbers456", "_89testing123numbers456")
        self.check_name_valid("", "_")
        self.check_name_valid("àâáäãåÀÂÁÃÅÄ", "aaaaaaAAAAAA")
        self.check_name_valid("èêéëÈÊÉË", "eeeeEEEE")
        self.check_name_valid("ìîíïÌÎÍÏ", "iiiiIIII")
        self.check_name_valid("òôóöõøÒÔÓÕÖØ", "ooooooOOOOOO")
        self.check_name_valid("ùûúüÙÛÚÜ", "uuuuUUUU")
        self.check_name_valid("æœÆŒçÇ°ðÐñÑýÝþÞÿß", "aeoeAEOEcCdegdDnNyYthThyss")
        self.check_name_valid("!¡¿@#$%?&*()-_=+/\\`^~.,'\<>`;:¤{}[]|\"¦¨«»¬¯±´·¸÷",
                              "____________________________________________________")
        self.check_name_valid("¢£¥§©ªº®¹²³µ¶¼½¾×", "C_PSY_SS_c_ao_r_123uP_1_4_1_2_3_4x")

    def check_name_valid(self, source, expected):
        v: str = ext.USDtools.make_name_valid(source)
        self.assertEqual(v, expected, f"Expected \"{v}\", derived from \"{source}\", to equals \"{expected}\"")
