from __future__ import absolute_import

import re

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor


class RemoveProgressProcessor(LineTransformProcessor):

    def __init__(self):
        super(RemoveProgressProcessor, self).__init__()
        self.code_map = {
            re.compile("[^;(]*[mM]73"): self._transform_m73,
        }

    def _transform_m73(self, input_line):
        return ""
