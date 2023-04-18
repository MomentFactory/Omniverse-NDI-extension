import omni.kit.test
from ..NDItools import NDIData
from .test_utils import SOURCE1


class NDIDataUnitTest(omni.kit.test.AsyncTestCase):
    async def test_source(self):
        data = NDIData(SOURCE1, False)
        self.assertEqual(data.get_source(), SOURCE1)

    async def test_active(self):
        data = NDIData(SOURCE1)
        self.assertFalse(data.is_active())

        data = NDIData(SOURCE1, False)
        self.assertFalse(data.is_active())

        data = NDIData(SOURCE1, True)
        self.assertTrue(data.is_active())

        data.set_active(False)
        self.assertFalse(data.is_active())

        data.set_active(True)
        self.assertTrue(data.is_active())
