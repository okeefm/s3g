"""
Inserts progress commands in skeinforge gcode
"""
from __future__ import absolute_import

from .Preprocessor import *

class ProgressPreprocessor(Preprocessor):
    
    def __init__(self):
        self.command = re.compile('([A-Z]\d+(\.\d+)? )+')

    def get_percent(self, count_current, count_total):
        decimal = 1.0 * count_current / count_total
        percent = int(decimal*100)
        return percent

    def create_progress_msg(self, percent):
        progressmsg = "M73 P%s (progress (%s%%))\n" % (percent, percent)
        return progressmsg
    
    def process_file(self, inlines):
        output = []
        count_total = len(inlines)
        count_current = 0
        current_percent = 0
        for line in inlines:
            count_current += 1
            output.append(line)
            new_percent = self.get_percent(count_current, count_total)
            if new_percent > current_percent:
                progressmsg = self.create_progress_msg(new_percent)
                output.append(progressmsg)
                current_percent = new_percent
        return output

def main():
    ProgressPreprocessor().process_file(sys.argv[1], sys.argv[2])

if __name__=="__main__":
    sys.exit(main())
