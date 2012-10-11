"""
Inserts progress commands in skeinforge gcode
"""
from __future__ import absolute_import

from .Processor import *


class ProgressProcessor(Processor):

    def __init__(self):
        super(ProgressProcessor, self).__init__()
        self.command = re.compile('([A-Z]\d+(\.\d+)? )+')

    def create_progress_msg(self, percent):
        progressmsg = "M73 P%s (progress (%s%%))\n" % (percent, percent)
        return progressmsg

    def process_gcode(self, gcodes, callback=None):
        output = []
        count_total = len(gcodes)
        count_current = 0
        current_percent = 0
        for code in gcodes:
            count_current += 1
            output.append(code)
            new_percent = self.get_percent(count_current, count_total)
            if new_percent > current_percent:
                progressmsg = self.create_progress_msg(new_percent)
                self.test_for_external_stop()
                with self._condition:
                    output.append(progressmsg)
                current_percent = new_percent
                if callback is not None:
                    callback(current_percent)
        return output


def main():
    ProgressProcessor().process_gcode(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    sys.exit(main())
