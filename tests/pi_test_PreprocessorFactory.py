import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import makerbot_driver

class TestPreprocessorFactory(unittest.TestCase):

  def setUp(self):
    self.f = makerbot_driver.Preprocessors.PreprocessorFactory()

  def tearDown(self):
    self.f = None

  def test_list_preprocessors(self):
    prepros = makerbot_driver.Preprocessors.all
    self.assertEqual(prepros, self.f.list_preprocessors())

  def test_create_preprocessor_from_name_not_a_preprocessor(self):
    prepro = 'THIS ISNT A VALID PREPROCESSOR NAME'
    self.assertRaises(makerbot_driver.Preprocessors.PreprocessorNotFoundError, self.f.create_preprocessor_from_name, prepro)

  def test_create_preprocessor_from_name(self):
    skeinforge_prepro = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
    expected_class = skeinforge_prepro.__class__
    got_prepro = self.f.create_preprocessor_from_name('Skeinforge50Preprocessor')
    got_class = got_prepro.__class__
    self.assertEqual(expected_class, got_class)

  def test_create_multiple_prepros_no_prepros(self):
    got_prepros = list(self.f.get_preprocessors([]))
    self.assertEqual(0, len(got_prepros))

  def test_get_preprocessors_one_prepro(self):
    skeinforge_prepro = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
    expected_class = skeinforge_prepro.__class__
    desired_prepro = 'Skeinforge50Preprocessor'
    got_prepros = list(self.f.get_preprocessors(desired_prepro))
    self.assertEqual(1, len(got_prepros))
    self.assertEqual(expected_class, got_prepros[0].__class__)

  def test_process_list_with_commas(self):
    cases = [
        ['a, b, c, d, ', ['a', 'b', 'c', 'd']],
        ['a,b,c,d,e,', ['a', 'b', 'c', 'd', 'e']],
        ['a, b, c, d,e', ['a','b','c','d','e']],
        ]
    for case in cases:  
      self.assertEqual(case[1], self.f.process_list_with_commas(case[0]))

  def test_get_preprocessors_multiple_prepros(self):
    desired_prepros = 'Skeinforge50Preprocessor, RpmPreprocessor, SlicerPreprocessor'
    got_prepros = list(self.f.get_preprocessors(desired_prepros))
    expected_prepros = [
        makerbot_driver.Preprocessors.Skeinforge50Preprocessor(),
        makerbot_driver.Preprocessors.RpmPreprocessor(),
        makerbot_driver.Preprocessors.SlicerPreprocessor(),
        ]
    self.assertEqual(len(expected_prepros), len(got_prepros))
    for expect, got in zip(expected_prepros, got_prepros):
      self.assertEqual(expect.__class__, got.__class__)

if __name__ == '__main__':
  unittest.main()
