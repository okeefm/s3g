"""
An interface that all future preprocessors should inherit from
"""

class Preprocessor(object):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    pass
