"""
Inserts progress commands in skeinforge gcode
"""

import os
import sys
import re
from Preprocessor import *


class ProgressPreprocessor(Preprocessor):

    def __init__(self):
        self.command = re.compile('([A-Z]\d+(\.\d+)? )+')
        self.countTotal = 1
        self.countCurrent = 0

    def count_commands(self, infh):
        self.countTotal = 1
        self.countCurrent = 0
        for line in infh:
            if self.command.match(line):
                self.countTotal += 1

    def print_progress(self, outfh):
        curPercent = int((self.countCurrent * 100) / self.countTotal)
        lastPercent = int(((self.countCurrent - 1) * 100) / self.countTotal)
        if lastPercent != curPercent:
            progressmsg = "M73 P%s (progress (%s%%): %s/%s)\n" % (
                curPercent, curPercent, self.countCurrent, self.countTotal)
            outfh.write(progressmsg)

    def process_file(self, input_path, output_path):
        self.inputs_are_gcode(input_path, output_path)
        with open(input_path, 'r') as infh:
            with open(output_path, 'w') as outfh:
                self.count_commands(infh)
                infh.seek(0)
                for line in infh:
                    if self.command.match(line):
                        self.countCurrent += 1
                        self.print_progress(outfh)
                    outfh.write(line)


def main():
    ProgressPreprocessor().process_file(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    sys.exit(main())
