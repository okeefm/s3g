from __future__ import absolute_import

import makerbot_driver

class PreProFactory(object):

  def __init__(self):
    pass

  def list_preprocessors(self):
    prepros = makerbot_driver.Preprocessors.all
    if 'errors' in prepros:
      prepros.remove('errors')
    return prepros

  def create_preprocessor_from_name(self, name):
    try:
      return getattr(makerbot_driver.Preprocessors, name)()
    except AttributeError:
      raise makerbot_driver.Preprocessors.PreprocessorNotFoundError

  def process_list_with_commas(self, string):
    string = string.replace(' ', '')
    strings = string.split(',')
    for s in strings:
      if s == '':
        strings.remove(s)
    return strings 

  def get_preprocessors(self, preprocessors):
    if isinstance(preprocessors, str):
      preprocessors = self.process_list_with_commas(preprocessors)
    for preprocessor in preprocessors:
      yield self.create_preprocessor_from_name(preprocessor)
