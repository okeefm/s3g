import re
import inspect

from .LineTransformProcessor import LineTransformProcessor
from .ProgressProcessor import ProgressProcessor


class BundleProcessor(LineTransformProcessor):

    def __init__(self):
        super(BundleProcessor, self).__init__()
        self.processors = []
        self.code_map = {}
        # Held here for testing purposes
        self._super_process_gcode = super(BundleProcessor, self).process_gcode

    def collate_codemaps(self):
        transform_code = "_transform_"
        for processor in self.processors:
            if processor.is_bundleable:
                self.code_map.update(processor.code_map)

    def process_gcode(self, gcodes, gcode_info, callback=None):
        self.callback = callback
        new_callback = None

        self.collate_codemaps()

        if self.callback is not None:
            new_callback = self.new_callback
        for code in self._super_process_gcode(gcodes, gcode_info, new_callback):
            yield code

    def set_external_stop(self, value=True):
        super(BundleProcessor, self).set_external_stop(value)
        with self._condition:
            self.progress_processor.set_external_stop(value)

    def new_callback(self, percent):
        """
        Since we do two passes with percent, we only want the
        first percent to go up to 50.
        """
        self.callback(percent / 2)

    def progress_callback(self, percent):
        """
        Since we do two passes with percent, we want the
        second percent to go up to 100
        """
        self.callback(50 + percent / 2)
