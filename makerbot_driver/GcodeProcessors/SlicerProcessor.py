from __future__ import absolute_import

import makerbot_driver
from .BundleProcessor import BundleProcessor
from .RpmProcessor import RpmProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .AbpProcessor import AbpProcessor
from .ProgressProcessor import ProgressProcessor


class SlicerProcessor(BundleProcessor):

  def __init__(self):
    super(SlicerProcessor, self).__init__()
    self.processors = [
        RpmProcessor(),
        CoordinateRemovalProcessor(),
        AbpProcessor(),
        ProgressProcessor(),
        ]
