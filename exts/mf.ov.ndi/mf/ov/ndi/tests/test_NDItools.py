import omni.kit.test
import mf.ov.ndi as ext


SOURCE = "MY-PC (Test Pattern)"


class NDIDataUnitTest(omni.kit.test.AsyncTestCase):
    async def test_source(self):
        data = ext.NDIData(SOURCE, False)
        self.assertEqual(data.get_source(), SOURCE)

    async def test_active(self):
        data = ext.NDIData(SOURCE)
        self.assertFalse(data.is_active())

        data = ext.NDIData(SOURCE, False)
        self.assertFalse(data.is_active())

        data = ext.NDIData(SOURCE, True)
        self.assertTrue(data.is_active())

        data.set_active(False)
        self.assertFalse(data.is_active())

        data.set_active(True)
        self.assertTrue(data.is_active())
