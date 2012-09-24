from errors import *
from .. import Gcode
from Preprocessor import *


class RemoveRepGStartEndGcode(Preprocessor):

    def __init__(self):
        pass

    def process_file(self, input_path, output_path):
        self.inputs_are_gcode(input_path, output_path)
        startgcode = False
        endgcode = False

        output = open(output_path, 'w')
        with open(input_path) as f:
            for line in f:
                if startgcode:
                    if(self.get_comment_match(line, 'end of start.gcode')):
                        startgcode = False
                elif endgcode:
                    if(self.get_comment_match(line, 'end End.gcode')):
                        endgcode = False
                else:
                    if (self.get_comment_match(line, '**** start.gcode')):
                        startgcode = True
                    elif (self.get_comment_match(line, '**** End.gcode')):
                        endgcode = True
                    else:
                        output.write(line)
        output.close()

    def get_comment_match(self, input_line, match):
        (codes, flags, comments) = Gcode.parse_line(input_line)
        axis = None
        if comments.find(match) is -1:
            return False
        else:
            return True
