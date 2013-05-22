from __future__ import absolute_import

import re
import makerbot_driver

from .LineTransformProcessor import LineTransformProcessor

class RemoveMGStartPositionProcessor(LineTransformProcessor):
    """
        This processor removes the first move in a Miracle-Grue gcode file.
        This is done as of MakerWare2.2, since moving to the start position mid-dualstrusion
        print causes issues. This processor works under the assumption that the first G1
        command is the start position command
    """
    def __init__(self):
        super(RemoveMGStartPositionProcessor, self).__init__()
        self.code_map = {
            re.compile('^G1'): self._handle_move
        }
        self.seeking_first_move = True

    def _handle_move(self, match):
        if self.seeking_first_move:
            self.seeking_first_move = False            
            return []
        else:
            return [match.string]
