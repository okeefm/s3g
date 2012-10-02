"""
A set of preprocessors for the skeinforge engine
"""
from __future__ import absolute_import

import re

from .BundleProcessor import BundleProcessor
from .LineTransformProcessor import LineTransformProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .TemperatureProcessor import TemperatureProcessor
from .RpmProcessor import RpmProcessor

import makerbot_driver


class Skeinforge50Processor(BundleProcessor):
    """
    A Processor that takes a skeinforge 50 file without start/end
    and replaces/removes deprecated commands with their replacements.
    """
    def __init__(self):
        super(Skeinforge50Processor, self).__init__()
        self.version = 50
        self.processors = [
            CoordinateRemovalProcessor(),
            TemperatureProcessor(),
            RpmProcessor(),
            SkeinforgeVersionChecker(self.version),
        ]
        self.code_map = {}


class SkeinforgeVersionChecker(LineTransformProcessor):

    def __init__(self, version):
        super(SkeinforgeVersionChecker, self).__init__()
        self.version = version
        self.code_map = {
            re.compile(".*using Skeinforge \("): self._check_version,
        }

    def _check_version(self, input_line):
        match = re.match(".*using Skeinforge \((.*?)\)", input_line)
        if int(match.group(1)) is not self.version:
            raise makerbot_driver.GcodeProcessors.VersionError
        return input_line
