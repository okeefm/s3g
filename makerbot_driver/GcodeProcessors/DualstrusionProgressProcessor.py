from __future__ import absolute_import

from .LineTransformProcessor import LineTransformProcessor
import makerbot_driver

import re

class DualstrusionProgressProcessor(LineTransformProcessor):

    def __init__(self):
        super(DualstrusionProgressProcessor, self).__init__()
        self.is_bundleable = False
        self.code_map = {
            re.compile("[^(;]*([(][^)]*[)][^(;]*)*[mM]73 P([\d/.]*)"): self._transform_progress_update
        }
        self.total_progress = 0.0

    def _transform_progress_update(self, match):
        codes = []
        progress = float(match.group(2))
        # We only want to process whole numbers
        if progress % 1 == 0:
            self.total_progress += .5
            msg = makerbot_driver.GcodeProcessors.ProgressProcessor.create_progress_msg(min(99, self.total_progress))
            codes.append(msg)
        return codes
