from __future__ import absolute_import
import re

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor


class TemperatureProcessor(LineTransformProcessor):

    def __init__(self):
        super(TemperatureProcessor, self).__init__()
        self.is_bundleable = True
        self.code_map = {
            re.compile("[^;(]*([(][^)]*[)][^(;]*)*[mM]104"): self._transform_m104,
            re.compile("[^;(]*([(][^)]*[)][^(;]*)*[mM]105"): self._transform_m105,
        }

    def _transform_m104(self, match):
        return ""

    def _transform_m105(self, match):
        return ""
