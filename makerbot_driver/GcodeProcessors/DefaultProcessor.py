"""
The Default Preprocessor is a preprocessor
that runs several sub-preprocessors to cover
common problems that most gcode files have.
"""
from __future__ import absolute_import

import makerbot_driver
from .BundleProcessor import BundleProcessor
from .ToolchangeProcessor import ToolchangeProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor


class DefaultProcessor(BundleProcessor):

    def __init__(self):
        super(DefaultProcessor, self).__init__()
        self.processors = [
            ToolchangeProcessor(),
            CoordinateRemovalProcessor(),
        ]
        self.do_progress = False
