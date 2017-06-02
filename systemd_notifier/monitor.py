import atexit
import logging
import Queue
import threading

from callback import CallbackManager
from notification import NotificationCenter, Notification

class Monitor(object):

    def __init__(self, hostname, dbus_manager, notification_center):
        self._hostname                   = hostname
        self._dbus_manager               = dbus_manager
        self._notification_center        = notification_center
        self._units                      = []
        self._state_queue                = Queue.Queue()
        self._callback_manager           = CallbackManager(self._state_queue)
        self._change_callback            = lambda unit: self._unit_change_callback(unit)
        self._each_state_change_callback = None

    def add_notifier(self, notifier):
        self._notification_center.add_notifier(notifier)

    def register_unit(self, unit_name):
        unit = self._dbus_manager.fetch_unit(unit_name)
        self._units.append(unit)
        return self

    def register_units(self, unit_names):
        for unit_name in unit_names:
            self.register_unit(unit_name)
        return self

    def on_change(self, callback):
        self._change_callback = callback
        return self

    def on_each_state_change(self,callback):
        self._each_state_change_callback = callback
        return self

    def start(self):
        logging.info("Monitoring changes to %d units"%(len(self._units)))
        logging.debug(" - " + "\n - ".join([u.name for u in self._units]) + "\n")

        atexit.register(lambda: self._notification_center.notify_stop(self._hostname))
        self._notification_center.notify_start(self._hostname)

        for unit in self._units:
            unit.register_listener(self._state_queue)

        threads = [self._start_callback_thread(), self._start_dbus_thread()]
        for t in threads:
            t.join(1000000)

    def _start_dbus_thread(self):
        return self._start_thread(target = lambda: self._dbus_manager.runner.run())

    def _start_callback_thread(self):
        return self._start_thread(target = lambda: self._callback_manager.start(self._change_callback, self._each_state_change_callback))

    def _start_thread(self, target):
        t = threading.Thread(target = target)
        t.daemon = True
        t.start()
        return t

    def _unit_change_callback(self, unit):
        logging.debug("[%s] %s: %s %s"%(unit.name, unit.state_change.status_text,
                                        unit.state.active, unit.state.sub))
        logging.debug("[%s] \n%s"%(unit.name, str(unit.state_change)))
        self._notification_center.notify(Notification(self._hostname, unit))
