from ..USDtools import USDtools
from .test_utils import make_stage, close_stage, create_dynamic_material, create_dynamic_rectlight, SOURCE1

import omni.kit.test


class USDValidNameUnitTest(omni.kit.test.AsyncTestCase):
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
        self.check_name_valid("!¡¿@#$%?&*()-_=+/`^~.,'\\<>`;:¤{}[]|\"¦¨«»¬¯±´·¸÷",
                              "___________________________________________________")
        self.check_name_valid("¢£¥§©ªº®¹²³µ¶¼½¾×", "C_PSY_SS_c_ao_r_123uP_1_4_1_2_3_4x")

    def check_name_valid(self, source, expected):
        v: str = USDtools.make_name_valid(source)
        self.assertEqual(v, expected, f"Expected \"{v}\", derived from \"{source}\", to equals \"{expected}\"")


class USDToolsUnitTest(omni.kit.test.AsyncTestCase):
    def setUp(self):
        self._stage = make_stage()

    def tearDown(self):
        close_stage()

    async def test_create_dynamic_material(self):
        material = create_dynamic_material()
        prim = self._stage.GetPrimAtPath(material.GetPath())
        self.assertIsNotNone(prim)

    async def test_find_dynamic_sources(self):
        create_dynamic_material()
        create_dynamic_rectlight()

        sources = USDtools.find_all_dynamic_sources()
        self.assertEqual(len(sources), 2)

    async def test_set_property_ndi(self):
        material = create_dynamic_material()
        path = material.GetPath()
        USDtools.set_prim_ndi_attribute(path, SOURCE1)

        attr = material.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
        self.assertEqual(attr.Get(), SOURCE1)

    async def test_set_property_bandwidth(self):
        material = create_dynamic_material()
        path = material.GetPath()
        USDtools.set_prim_lowbandwidth_attribute(path, True)

        attr = material.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
        self.assertTrue(attr.Get())

        USDtools.set_prim_lowbandwidth_attribute(path, False)
        self.assertFalse(attr.Get())
