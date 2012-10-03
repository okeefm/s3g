from __future__ import absolute_import
import re
import math
import contextlib

from .LineTransformProcessor import LineTransformProcessor
import makerbot_driver


class AnchorProcessor(LineTransformProcessor):
    def __init__(self):
        super(AnchorProcessor, self).__init__()
        self.code_map = {
            re.compile('[^(;]*([(][^)]*[)][^(;]*)*[gG]1 '): self._transform_anchor,
        }
        self.looking_for_first_move = True

    def _transform_anchor(self, match):
        return_lines = [match.string]
        if self.looking_for_first_move:
            start_position = self.get_start_position()
            return_lines = list(
                self.create_anchor_command(start_position, return_lines[0]))
            return_lines.append(match.string)
            self.looking_for_first_move = False
        return return_lines

    def create_anchor_command(self, start_position, end_position):
        assert start_position is not None and end_position is not None
        start_movement_codes = makerbot_driver.Gcode.parse_line(
            start_position)[0]
        end_movement_codes = makerbot_driver.Gcode.parse_line(end_position)[0]
        # We dont really know what the next command contains; it could have all or
        # none of the following, so we need to generate the next command in this
        # seemingly bad way
        anchor_command = "G1 "
        for d in ['X', 'Y', 'Z']:
            if d in end_movement_codes:
                part = d + str(end_movement_codes[d])
                anchor_command += part
                anchor_command += ' '
        anchor_command += 'F%i ' % (1000)
        extruder = self.get_extruder(end_movement_codes)
        extrusion_distance = self.find_extrusion_distance(
            start_movement_codes, end_movement_codes)
        anchor_command += extruder + str(extrusion_distance) + "\n"
        reset_command = "G92 %s0" % (extruder) + "\n"
        return anchor_command, reset_command

    def get_extruder(self, codes):
        extruder = 'A'
        if 'B' in codes:
            extruder = 'B'
        elif 'E' in codes:
            extruder = 'E'
        return extruder

    def find_extrusion_distance(self, start_position_codes, end_position_codes):
        start_position_point = []
        end_position_point = []
        for d in ['X', 'Y', 'Z']:
            start_position_point.append(start_position_codes.get(d, 0))
            end_position_point.append(end_position_codes.get(d, 0))
        distance = self.calc_euclidean_distance(
            start_position_point, end_position_point)
        layer_height = end_position_point[2]
        width_over_height = 1.6
        cross_section = self.feed_cross_section_area(
            float(layer_height), width_over_height)
        extrusion_distance = cross_section * distance
        return extrusion_distance

    def feed_cross_section_area(self, height, width):
        """
        Taken from MG, (hopefully not wrongfully) assumed to work
        """
        radius = height / 2.0
        tau = math.pi
        return (tau / 2.0) * (radius * radius) + height * (width - height)

    def calc_euclidean_distance(self, p1, p2):
        assert len(p1) == len(p2)
        distance = 0.0
        for a, b in zip(p1, p2):
            distance += pow(a - b, 2)
        distance = math.sqrt(distance)
        return distance

    def get_start_position(self):
        return "G1 X-112 Y-73 Z150 F3300.0 (move to waiting position)"
