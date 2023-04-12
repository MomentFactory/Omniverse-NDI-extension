import omni.kit.test
from ..NDItools import NDIData
from ..model import NDIBinding, NDIModel
from ..USDtools import USDtools
from ..comboboxModel import ComboboxModel
from .test_utils import SOURCE1, SOURCE2, DYNAMIC_ID1, DYNAMIC_ID2, DUMMY_PATH


class NDIBindingsUnitTest(omni.kit.test.AsyncTestCase):
    async def test_dynamic_id(self):
        ndi_data = NDIData(SOURCE1)
        ndi_binding = NDIBinding(DYNAMIC_ID1, ndi_data, DUMMY_PATH, False)

        self.assertEqual(ndi_binding.get_id(), DYNAMIC_ID1)
        self.assertEqual(ndi_binding.get_id_full(), USDtools.PREFIX + DYNAMIC_ID1)

    async def test_source(self):
        ndi_data1 = NDIData(SOURCE1)
        ndi_data2 = NDIData(SOURCE2)

        ndi_binding = NDIBinding(DYNAMIC_ID1, ndi_data1, DUMMY_PATH, False)
        self.assertEqual(ndi_binding.get_source(), SOURCE1)

        ndi_binding.set_ndi_id(ndi_data2)
        self.assertEqual(ndi_binding.get_source(), SOURCE2)

    async def test_lowbandwidth(self):
        ndi_data = NDIData(SOURCE1)
        ndi_binding = NDIBinding(DYNAMIC_ID1, ndi_data, DUMMY_PATH, False)
        self.assertFalse(ndi_binding.get_lowbandwidth())

        ndi_binding = NDIBinding(DYNAMIC_ID1, ndi_data, DUMMY_PATH, True)
        self.assertTrue(ndi_binding.get_lowbandwidth())

        ndi_binding.set_lowbandwidth(False)
        self.assertFalse(ndi_binding.get_lowbandwidth())
        ndi_binding.set_lowbandwidth(True)
        self.assertTrue(ndi_binding.get_lowbandwidth())
        pass


class ModelUnitTest(omni.kit.test.AsyncTestCase):
    def setUp(self):
        self._model = NDIModel(None)

    def tearDown(self):
        self._model.on_shutdown()

    async def test_no_stream_at_start(self):
        streams_length = len(self._model._streams)
        self.assertEqual(streams_length, 0)

    async def test_add_stream_NONE(self):
        streams_base_length = len(self._model._streams)

        self._model.add_stream(DYNAMIC_ID1, ComboboxModel.NONE_VALUE, False)
        self.assertEqual(len(self._model._streams), streams_base_length)

    async def test_add_stream_PROXY(self):
        streams_length = len(self._model._streams)

        self._model.add_stream(DYNAMIC_ID1, ComboboxModel.PROXY_VALUE, False)
        self.assertEqual(len(self._model._streams), streams_length + 1)

    async def test_kill_all_streams(self):
        self._model.add_stream(DYNAMIC_ID1, ComboboxModel.PROXY_VALUE, False)
        self._model.add_stream(DYNAMIC_ID2, ComboboxModel.PROXY_VALUE, False)
        self.assertGreater(len(self._model._streams), 0)

        self._model.kill_all_streams()
        self.assertEqual(len(self._model._streams), 0)

    async def test_remove_stream(self):
        self._model.add_stream(DYNAMIC_ID1, ComboboxModel.PROXY_VALUE, False)
        self._model.add_stream(DYNAMIC_ID2, ComboboxModel.PROXY_VALUE, False)
        streams_length = len(self._model._streams)
        self.assertGreater(streams_length, 0)

        self._model.remove_stream(DYNAMIC_ID1, ComboboxModel.PROXY_VALUE)
        self.assertEqual(len(self._model._streams), streams_length - 1)
        self._model.remove_stream(DYNAMIC_ID1, ComboboxModel.PROXY_VALUE)
        self.assertEqual(len(self._model._streams), streams_length - 1)
        self._model.remove_stream(DYNAMIC_ID2, ComboboxModel.PROXY_VALUE)
        self.assertEqual(len(self._model._streams), streams_length - 2)


"""
    async def test_add_stream(self):
        model = NDIModel(None)
        streams_length = len(model._streams)

        model.add_stream(DYNAMIC_ID, SOURCE1, False)
        self.assertEqual(len(model._streams), streams_length + 1)
        model.add_stream(DYNAMIC_ID, SOURCE2, False)
        self.assertEqual(len(model._streams), streams_length + 2)
"""
