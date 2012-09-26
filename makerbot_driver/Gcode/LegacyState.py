from __future__ import absolute_import

import makerbot_driver
from .States import State


class LegacyState(State):

    def lose_position(self, axes):
        self._log.debug(
            '{"event":"gcode_state_change", "change":"lose_position"}')
        for axis in axes:
            setattr(self.position, axis, 0)
