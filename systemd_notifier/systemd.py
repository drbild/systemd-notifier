import dbus
import dbus.mainloop.glib
import gobject

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
gobject.threads_init()

from state import State
from error import SystemdError, UnknownUnitError

class DBusManager(object):

    def __init__(self):
        self.system_bus     = dbus.SystemBus()
        self.systemd_object = self.system_bus.get_object('org.freedesktop.systemd1',
                                                         '/org/freedesktop/systemd1')
        self.systemd_manager = dbus.Interface(self.systemd_object, dbus_interface='org.freedesktop.systemd1.Manager')
        try:
            self.systemd_manager.Subscribe()
        except dbus.DBusException as e:
            raise SystemdError("Systemd is not installed, or is an incompatable version. It must provide the Subscribe dbus method: version 204 is the minimum recommended version.", e)
      
    def fetch_unit(self, unit_name):
        try:
            unit_path   = self.systemd_manager.LoadUnit(unit_name)
            unit_object = self.system_bus.get_object('org.freedesktop.systemd1', str(unit_path))
            return DBusUnit(unit_name, unit_path, unit_object)
        except dbus.DBusException as e:
            raise UnknownUnitError("Unknown or unloaded systemd unit '%s'"%(unit_name), e)

    @property
    def runner(self):
        gobject.MainLoop().run()

class DBusUnit(object):

    IFACE_UNIT    = "org.freedesktop.systemd1.Unit"
    IFACE_SERVICE = "org.freedesktop.systemd1.Service"
    IFACE_PROPS   = "org.freedesktop.DBus.Properties"

    def __init__(self, name, path, dbus_object):
        self._name               = name
        self._path               = path
        self._dbus_object        = dbus_object
        self._maybe_service_type = self._service_type()

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def dbus_object(self):
        return self._dbus_object

    @property
    def maybe_service_type(self):
        return self._maybe_service_type

    def register_listener(self, queue):
        self._enqueue_state(queue)
        self.dbus_object.connect_to_signal("PropertiesChanged",
                                           lambda iface, *args: self._enqueue_state(queue) if iface == DBusUnit.IFACE_UNIT else None,
                                           dbus_interface = DBusUnit.IFACE_PROPS)

    def on_change(self, callback):
        self._change_callback = callback

    def on_each_state_change(self, callback):
        self._each_state_change_callback = callback

    def property(self, name):
        return self.dbus_object.Get(DBusUnit.IFACE_UNIT, name, dbus_interface=DBusUnit.IFACE_PROPS)

    def __str__(self):
        if self.maybe_service_type:
            type_label = " (%s)"%(self.maybe_service_type,)
        else:
            type_label = ""
        return "{name}{type_label}".format(name = self._name, type_label = type_label)

    def _build_state(self):
        return State(self.property('ActiveState'),
                     self.property('SubState'),
                     self.property('LoadState'),
                     self.property('UnitFileState'),
                     self.maybe_service_type)

    def _enqueue_state(self, queue):
        queue.put((self, self._build_state()))
    
    def _service_type(self):
        service_props = self.dbus_object.GetAll(DBusUnit.IFACE_SERVICE, dbus_interface=DBusUnit.IFACE_PROPS)
        if 'Type' in service_props:
            return service_props['Type']
        else:
            return None
