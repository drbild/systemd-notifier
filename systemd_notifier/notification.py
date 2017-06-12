import logging
import threading

def load_notifier(name):
    import importlib

    def camel_case(name):
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    module = importlib.import_module("systemd_notifier.notifiers.%s"%camel_case(name.capitalize()))
    return getattr(module, name.capitalize())

class Notification(object):

    def __init__(self, hostname, unit):
        self._hostname = hostname
        self._unit     = unit

    @property
    def hostname(self):
        return self._hostname

    @property
    def unit(self):
        return self._unit

    @property
    def name(self):
        return type(self)

    @property
    def type(self):
        if self.unit.state_change.is_ok:
            if self.unit.state_change.states[0].is_failure:
                return "ok"
            else:
                return "info"
        else:
            return "alert"

class NotificationCenter(object):

    def __init__(self):
        self._notifiers = []

    def add_notifier(self, notifier):
        self._notifiers.append(notifier)

    def notify(self, notification):
        def do_notify(notifier):
            logging.debug("Notifying state change of %s via %s", notification.unit.name, notifier.name)
            notifier.notify(notification)
            
        self._for_each_notifier(do_notify)

    def notify_start(self, hostname):
        logging.info("Systemd Notifier started.")
        def do_notify_start(notifier):
            logging.debug("Notifying systemd_notifier start via %s"%(notifier.name))
            notifier.notify_start(hostname)

        self._for_each_notifier(do_notify_start)

    def notify_stop(self, hostname):
        logging.info("Systemd Notifier stopped.")
        def do_notify_stop(notifier):
            logging.debug("Notifying systemd_notifier stop via %s"%(notifier.name))
            notifier.notify_stop(hostname)

        self._for_each_notifier(do_notify_stop)
        
    def _for_each_notifier(self, callable):
        def callable_safe(notifier):
            try:
                callable(notifier)
            except Exception as e:
                logging.error("Failed to send notification via %s.", notifier.name, exc_info=True)

        threads = []
        for notifier in self._notifiers:
            t = threading.Thread(target=lambda: callable_safe(notifier))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
