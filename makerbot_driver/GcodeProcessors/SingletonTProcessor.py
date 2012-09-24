from __future__ import absolute_import

import re

import makerbot_driver
from .LineTransformProcessor import LineTransformProcessor 

class SingletonTProcessor(LineTransformProcessor):

  def __init__(self):
    super(SingletonTProcessor, self).__init__()
    self.code_map = { 
        re.compile(" *[tT][0-9] *[;(.*]*") : self._transform_singleton
        }
    self.singleton_search = re.compile(" *[tT][0-9]")

  def _transform_singleton(self, input_line):
    m = re.match(self.singleton_search, input_line)
    the_match = m.group()
    return_line = 'M135 T%s\n' %(the_match[-1])
    return return_line
