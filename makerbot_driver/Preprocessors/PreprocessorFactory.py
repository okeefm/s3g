from .. import Preprocessors

class PreProFactory(object):

  def __init__(self):
    pass

  def list_preprocessors(self):
    prepros = Preprocessors.all
    if 'errors' in prepros:
      prepros.remove('errors')
    return prepros

  def create_preprocessor_from_name(self, name):
    return getattr(Preprocessors, name)()

  def process_list_of_preprocessors

  def get_preprocessors(self, preprocessors):
    if isinstance(preprocessors, str):
      preprocessors = preprocessors.replace(' ', '')
      preprocessors = preprocessors.split(',')
      for preprocessor in preprocessors:
        if preprocessor == '':
          preprocessors.remove(preprocessor)
    return_preprocessors = []
    for preprocessor in preprocessors:
