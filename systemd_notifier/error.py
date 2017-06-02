class Error(Exception):
    pass

class SystemdError(Error):
    pass

class MonitorError(Error):
    pass

class UnknownUnitError(Error):
    pass

class NotificationError(Error):
    pass

class NotifierDependencyError(Error):
    pass

class NotifierError(Error):
    pass
