from __future__ import absolute_import

import re

from .LineTransformProcessor import LineTransformProcessor

class Rep2XDualstrusionPurgeProcessor(LineTransformProcessor):

    def __init__(self):
        super(Rep2XDualstrusionPurgeProcessor, self).__init__()
        map_addendum = {
            re.compile('M135\s[tT]\d'): self._set_toolhead,
            re.compile('G1'): self._add_purge,
        }
        self.code_map.update(map_addendum)
        self.looking_for_first_move = True
        self.current_toolchange = None

    def _set_toolhead(self, match):
        self.current_toolchange = match.string
        return self.current_toolchange

    def _add_purge(self, match):
        toadd = []
        if self.looking_for_first_move:
                toadd.extend([
                        "M135 T0\n",
                        "G1 X-105.400 Y-74.000 Z0.270 F1800.000 (Right Purge Start)\n",
                        "G1 X105.400 Y-74.000 Z0.270 F1800.000 A25.000 (Right Purge)\n",
                        "M135 T1\n",
                        "G1 X105.400 Y-73.500 Z0.270 F1800.000 (Left Purge Start)\n",
                        "G1 X-105.400 Y-73.500 Z0.270 F1800.000 B25.000 (Left Purge)\n",
                        "G92 A0 B0 (Reset after purge)\n",
                ])
        self.looking_for_first_move = False
        return toadd + [self.current_toolchange, match.string]
