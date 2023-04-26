import carb.events
import omni.kit.app


class EventSystem():
    BINDINGS_CHANGED_EVENT = carb.events.type_from_string("mf.ov.ndi.BINDINGS_CHANGED_EVENT")
    COMBOBOX_CHANGED_EVENT = carb.events.type_from_string("mf.ov.ndi.COMBOBOX_CHANGED_EVENT")
    NDIFINDER_NEW_SOURCES = carb.events.type_from_string("mf.ov.ndi.NDIFINDER_NEW_SOURCES")
    COMBOBOX_SOURCE_CHANGE_EVENT = carb.events.type_from_string("mf.ov.ndi.COMBOBOX_SOURCE_CHANGE_EVENT")
    NDI_STATUS_CHANGE_EVENT = carb.events.type_from_string("mf.ov.ndi.NDI_STATUS_CHANGE_EVENT")
    STREAM_STOP_TIMEOUT_EVENT = carb.events.type_from_string("mf.ov.ndi.STREAM_STOP_TIMEOUT_EVENT")

    def subscribe(event: int, cb: callable) -> carb.events.ISubscription:
        bus = omni.kit.app.get_app().get_message_bus_event_stream()
        return bus.create_subscription_to_push_by_type(event, cb)

    def send_event(event: int, payload: dict = {}):
        bus = omni.kit.app.get_app().get_message_bus_event_stream()
        bus.push(event, payload=payload)
