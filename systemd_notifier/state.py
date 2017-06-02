import datetime

class StateValue(object):

    def __init__(self, name, value, timestamp, ok_states = [], failure_states = []):
        self._name = name
        self._value = value
        self._timestamp = timestamp
        self._ok_states = ok_states
        self._failure_states = failure_states

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def ok_states(self):
        return self._ok_states

    @property
    def failure_states(self):
        return self._failure_states

    @property
    def display_name(self):
        return self.name.capitalize()

    @property
    def is_important(self):
        return (self.value in self.ok_states) or (self.value in self.failure_states)

    @property
    def is_ok(self):
        if any(s for s in self.ok_states):
            return self.value in self.ok_states
        else:
            return True

    @property
    def is_failure(self):
        if any(s for s in self.failure_states):
            return self.value in self.failure_states
        else:
            return False

    def __repr__(self):
        return '''StateValue(name=%r, value=%r, timestamp=%r, ok_states=%r, failure_states=%r)'''%(
            self.name, self.value, self.timestamp, self.ok_states, self.failure_states)

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if not isinstance(other, StateValue):
            return False

        return self.value == other.value

class State(object):

    @staticmethod
    def active_states(type):
        if type == 'oneshot':
            return [['inactive'], ['failed']]
        else:
            return [['active'], ['inactive', 'failed']]

    @staticmethod
    def file_states(type):
        if type == 'oneshot':
            return [[], []]
        else:
            return [['enabled', 'linked-runtime', 'static'], ['disabled']]

    def __init__(self, active, sub, loaded, unit_file, type=None):
        timestamp = datetime.datetime.now()
        self._type   = type
        self._active = StateValue("active", active, timestamp, *State.active_states(type))
        self._sub    = StateValue("status", sub, timestamp)
        self._loaded = StateValue("loaded", loaded, timestamp, ['loaded'])
        self._unit_file = StateValue("file", unit_file, timestamp, *State.file_states(type))
        self._all_states = [self._active, self._sub, self._loaded, self.unit_file]

    @property
    def active(self):
        return self._active

    @property
    def sub(self):
        return self._sub

    @property
    def loaded(self):
        return self._loaded

    @property
    def unit_file(self):
        return self._unit_file

    @property
    def all_states(self):
        return self._all_states

    @property
    def type(self):
        return self._type

    @property
    def is_ok(self):
        return all(s.is_ok for s in self.all_states)

    @property
    def is_failure(self):
        return any(s.is_failure for s in self.all_states)

    def __iter__(self):
        return iter(self.all_states)

    def __repr__(self):
        return '''State(active=%r, sub=%r, loaded=%r, unit_file=%r, type=%r)'''%(
            self.active, self.sub, self.loaded, self.unit_file, self.type)

    def __str__(self):
        return "[" + ", ".join((str(s) for s in self.all_states)) + "]"

    def __eq__(self, other):
        if not isinstance(other, State):
            return False

        return self.all_states == other.all_states

class StateChange(object):

    def __init__(self, original_state = None):
        self._states = []
        if original_state:
            self._states.append(original_state)

    @property
    def states(self):
        return self._states

    @property
    def current_state(self):
        return self._states[-1]

    @property
    def changes(self):
        return self._states[1:]

    def record_change(self, state):
        self._states.append(state)
    
    @property
    def is_ok(self):
        return self.states[-1].is_ok

    @property
    def is_failure(self):
        return self.states[-1].is_failure
    
    @property
    def is_recovery(self):
        return self.states[0].is_failure and self.states[-1].is_ok

    @property
    def is_restart(self):
        return self.states[0].is_ok and self.states[-1].is_ok and any(s.active.value == 'deactivating' for s in self.changes)

    @property
    def is_auto_restart(self):
        return self.states[0].is_ok and self.states[-1].is_ok and any(s.sub.value == 'auto-restart' for s in self.changes)

    @property
    def is_reload(self):
        return self.states[0].is_ok and self.states[-1].is_ok and any(s.active.value == 'reloading' for s in self.changes)

    @property
    def is_still_failure(self):
        return len(self.states) > 1 and self.states[0].is_failure and self.states[-1].is_failure

    @property
    def is_important(self):
        if len(self.states) == 1:
            return self.states[0].is_failure
        else:
            return any(s[-1].is_important for s in self.diff())

    @property
    def status_text(self):
        if self.is_recovery:
            return "recovered"
        elif self.is_auto_restart:
            return "automatically restarted"
        elif self.is_restart:
            return "restarted"
        elif self.is_reload:
            return "reloaded"
        elif self.is_still_failure:
            return "still failed"
        elif self.is_failure:
            return "failed"
        else:
            return "started"
    
    def zipped(self):
        return zip(*(s.all_states for s in self._states))

    def diff(self):
        return [states for states in self.zipped() if not all(s.value == states[0].value for s in states)]

    def __str__(self):
        return reduce(lambda s, states: s +
                      "%s: changed from %s.\n"%(states[0].name,
                                                " to ".join(str(s.value) for s in states)),
                      self.diff(),
                      "")
