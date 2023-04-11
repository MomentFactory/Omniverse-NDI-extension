import omni.kit.test
from ..USDtools import USDtools
from pxr import UsdLux


SOURCE = "MY-PC (Test Pattern)"


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
        usd_context = omni.usd.get_context()
        usd_context.new_stage()
        # self._stage = Usd.Stage.CreateInMemory()

        self._stage = USDtools.get_stage()
        prim = self._stage.DefinePrim("/World")
        self._stage.SetDefaultPrim(prim)

    def tearDown(self):
        usd_context = omni.usd.get_context()
        usd_context.close_stage()

    async def test_create_dynamic_material(self):
        material = USDtools.create_dynamic_material("myDynamicMaterial")
        prim = self._stage.GetPrimAtPath(material.GetPath())
        self.assertIsNotNone(prim)

    async def test_find_dynamic_sources(self):
        USDtools.create_dynamic_material("myDynamicMaterial1")

        path: str = f"{self._stage.GetDefaultPrim().GetPath()}/myRectLight"
        light = UsdLux.RectLight.Define(self._stage, path)
        light.GetPrim().GetAttribute("texture:file").Set(f"{USDtools.PREFIX}/myDynamicMaterial2")

        sources = USDtools.find_all_dynamic_sources()
        self.assertEqual(len(sources), 2)

    async def test_set_property_ndi(self):
        material = USDtools.create_dynamic_material("myDynamicMaterial")
        path = material.GetPath()
        USDtools.set_prim_ndi_attribute(path, SOURCE)

        attr = material.GetPrim().GetAttribute(USDtools.ATTR_NDI_NAME)
        self.assertEqual(attr.Get(), SOURCE)

    async def test_set_property_bandwidth(self):
        material = USDtools.create_dynamic_material("myDynamicMaterial")
        path = material.GetPath()
        USDtools.set_prim_bandwidth_attribute(path, True)

        attr = material.GetPrim().GetAttribute(USDtools.ATTR_BANDWIDTH_NAME)
        self.assertTrue(attr.Get())

        USDtools.set_prim_bandwidth_attribute(path, False)
        self.assertFalse(attr.Get())
