import logging

from collections import defaultdict

from state import StateChange

class keydefaultdict(defaultdict):

    def __init__(self, default_factory, *args, **kwargs):
        super(keydefaultdict, self).__init__(None, *args, **kwargs)
        self.default_factory = default_factory
        
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret

class UnitWithState(object):

    def __init__(self, unit):
        self._unit         = unit
        self._state_change = StateChange()

    @property
    def unit(self):
        return self._unit

    @property
    def state_change(self):
        return self._state_change

    @property
    def name(self):
        return self.unit.name

    @property
    def current_state(self):
        return self._state_change.current_state

    @property
    def state(self):
        return self.current_state

    def record_change(self, state):
        self.state_change.record_change(state)

    def reset(self):
        logging.debug("%s start state: %s"%(self.unit, self.current_state))
        self._state_change = StateChange(self.current_state)
        
class CallbackManager(object):

    def __init__(self, queue):
        self._queue  = queue
        self._states = keydefaultdict(lambda u: UnitWithState(u))

    def start(self, change_callback, each_state_change_callback):
        while True:
            unit, state = self._queue.get()
            logging.debug("%s new state: %s"%(unit, state))
            unit_state = self._states[unit]
            unit_state.record_change(state)

            if each_state_change_callback:
                try:
                    each_state_change_callback(unit_state)
                except Exception as e:
                    logging.exception("Uncaught exception in callback: ", exc_info=True)

            if change_callback and unit_state.state_change.is_important:
                try:
                    change_callback(unit_state)
                except Exception as e:
                    logging.exception("Uncaught exception in callback: ", exc_info=True)

            if unit_state.state_change.is_important:
                unit_state.reset()
