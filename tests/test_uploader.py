import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import urlparse
import unittest
import io
import json
import mock
import urllib2
import tempfile

import s3g

class TestGetProducts(unittest.TestCase):
  def setUp(self):
     base_path = os.path.join(
         os.path.abspath(os.path.dirname(__file__)),
         'test_files',
         )
     self.uploader = s3g.Firmware.Uploader(base_url = base_path)
#     self.wget_mock = mock.Mock()
#     self.get_machine_json_files_mock = mock.Mock()
#     self.uploader.wget = self.wget_mock
#     self.uploader.get_machine_json_files = self.get_machine_json_files_mock 
 
  def tearDown(self):
    self.uploader = None
   
  def test_pathjoin(self):
    base, f = './base', 'x.txt'
    import os.path
    path = os.path.normpath(os.path.join(base,f))
    self.assertEquals(self.uploader.pathjoin(base,f), path) 
    base, f = 'http://base', 'x.txt'
    self.assertEquals(self.uploader.pathjoin(base,f), "http://base/x.txt")
 
  def test_pull_products(self):
    self.uploader._pull_products()	
    expected_products_url = self.uploader.pathjoin(self.uploader.base_url,'./products.json')
    #self.wget_mock.assert_called_once_with(expected_products_url)
    #self.get_machine_json_files_mock.assert_called_once_with() 
 
class TestWgetThis(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.check_call_mock = mock.Mock()
    self.uploader.run_subprocess = self.check_call_mock
    self.base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.uploader.base_path = self.base_path
    self.urlopen_mock = mock.Mock()
    self.uploader.urlopen = self.urlopen_mock

  def tearDown(self):
    self.uploader = None

  def test_wget(self):
    string = '1234567890asdf'
    class file_like_object(object):
      def __init__(self):
        pass
      def read(self):
        return string
    url = 'firmware.makerbot.com/foobar.json'
    filename = url.split('/')[-1]
    self.urlopen_mock.return_value = file_like_object()
    self.uploader.wget(url)
    self.urlopen_mock.assert_called_once_with(url)
    with open(os.path.join(self.base_path, filename)) as f:
      self.assertEqual(string, f.read())
    os.unlink(os.path.join(self.base_path, filename))
   
class TestGetMachineJsonFiles(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.wget_mock = mock.Mock()
    self.uploader.wget = self.wget_mock

  def tearDown(self):
    self.uploader = None

#  def test_get_machine_json_files_no_products(self):
#    self.assertRaises(AttributeError, self.uploader.get_machine_json_files)

  def test_get_machine_json_files_products_pulled_and_loaded(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files', 'products.json')) as f:
      self.uploader.products = json.load(f)
    self.uploader.get_machine_json_files()
    calls = self.wget_mock.mock_calls
    machines = self.uploader.products['ExtrusionPrinters']
    for machine, call in zip(machines, calls):
      filename = self.uploader.products['ExtrusionPrinters'][machine]
      firmware_url = urlparse.urljoin(self.uploader.base_url, filename)  
      self.assertEqual(firmware_url, call[1][0])

class TestGetFirmwareVersions(unittest.TestCase):

  def setUp(self):
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files', )
    self.uploader = s3g.Firmware.Uploader(base_url = base_path)
    self.uploader.base_path = base_path

  def tearDown(self):
    self.uploader = None

#  def test_list_firmware_versions_bad_machine_name(self):
#    self.assertRaises(
#        AttributeError, 
#        self.uploader.list_firmware_versions, 'I HOPE THIS ISNT A MACHINE NAME'
#        )

  def test_list_firmware_versions_good_machine_name(self):
    prodFile = os.path.join(self.uploader.base_path, 'products.json')
    with open(prodFile) as f:
      self.uploader.products = json.load(f)
    machine = 'Example'
    with open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'Example.json',
        )) as f:
      vals = json.load(f)
    expected_versions = []
    for version in vals['firmware']['versions']:
      descriptor = vals['firmware']['versions'][version][1]
      expected_versions.append([version, descriptor])
    got_versions = self.uploader.list_firmware_versions(machine)
    self.assertEqual(expected_versions, got_versions)

class TestGetFirmwareValues(unittest.TestCase):
  def setUp(self):
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
      )
    self.uploader = s3g.Firmware.Uploader(base_url = base_path)
    with open(os.path.join(base_path, 'products.json')) as f:
      self.uploader.products = json.load(f)

  def tearDown(self):
    self.uploader = None

  def test_get_firmware_values_bad_machine(self):
    machine = "i really hope you dont have a file with this exact name"
    self.assertRaises(KeyError, self.uploader.get_firmware_values, machine)
  

  def test_get_firmware_values_values(self):
    machine = "Example"
    with open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'Example.json'
        )) as f: 
      expected_values = json.load(f)
    self.assertEqual(expected_values, self.uploader.get_firmware_values(machine))

class TestListVersions(unittest.TestCase):
  def setUp(self):
    base_url = os.path.join('test_files')
    self.uploader = s3g.Firmware.Uploader(base_url = base_url)

#  def test_list_machines_no_products(self):
# #    self.assertRaises(AttributeError, self.uploader.list_machines)
# 
#   def test_list_machines(self):
#     with open(os.path.join(
#         self.uploader.base_path,
#         'test_files',
#         'products.json',
#         )) as f:
#       values = json.load(f)
#     self.uploader.products = values
#     expected_machines = []
#     for machine in values['ExtrusionPrinters']:
#        expected_machines.append(machine)
#     self.assertEqual(expected_machines, self.uploader.list_machines())
# 
class TestUploader(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.base_url = 'http://firmware.makerbot.com'


  def tearDown(self):
    self.uploader = None


  def test_update(self):
    update_mock = mock.Mock()
    self.uploader._pull_products = update_mock
    self.uploader.update()
    update_mock.assert_called_once_with()

  
  def test_load_json_values_good_file(self):
      path_to_json = os.path.join(os.path.abspath(os.path.dirname(__file__)),'test_files','products.json')
      with open(path_to_json) as f:
        expected_vals = json.load(f)
      got_vals = self.uploader.load_json_values(path_to_json)
      self.assertEqual(expected_vals, got_vals)

  def test_load_json_values_bad_file(self):
      filename = 'I HOPE THIS ISNT A FILENAME'
      self.assertRaises(IOError, self.uploader.load_json_values, filename)


class TestParseAvrdudeCommand(unittest.TestCase):
  def setUp(self):
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files', )
    self.uploader = s3g.Firmware.Uploader(base_url=base_path)
    
  def tearDown(self):
    self.uploader = None
 
#  def test_parse_avrdude_command_no_products(self):
#    port = '/dev/tty.usbmodemfa121'
#    machine = "Example"
#    version = '0.1'
#    self.assertRaises(AttributeError, self.uploader.parse_avrdude_command, port, machine, version)
 
  def test_parse_avrdude_command_cant_find_machine(self):
    with open(os.path.join(
        self.uploader.base_path,
        'products.json',
        )) as f:
      self.uploader.products = json.load(f)
    port = '/dev/tty.usbmodemfa121'
    machine = "i really hope you dont have a file with this exact name"
    version = '5.2'
    self.assertRaises(KeyError, self.uploader.parse_avrdude_command, port, machine, version)
 
  def test_parse_avrdude_command_cant_find_version(self):
    with open(os.path.join(
        self.uploader.base_path,
        'products.json',
        )) as f:
      self.uploader.products = json.load(f)
    port = '/dev/tty.usbmodemfa121'
    machine = 'Example'
    version = 'x.x'
    self.assertRaises(s3g.Firmware.UnknownVersionError, self.uploader.parse_avrdude_command, port, machine, version)
 

# def test_parse_avrdude_command(self):
#   wget_mock = mock.Mock()
#   self.uploader.wget = wget_mock
#   with open(os.path.join(
#       self.uploader.base_path,
#        'products.json',
#        )) as f:
#      self.uploader.products = json.load(f)
#   with open(os.path.join(self.uploader.base_path, 'Example.json')) as f:
#     example_profile = json.load(f)
#   example_values = example_profile['firmware']
#   port = '/dev/tty.usbmodemfa121'
#   machine = 'Example'
#   version = '0.1'
#   hex_url = example_values['versions'][version][0]
#   hex_path = os.path.join(
#       self.uploader.base_path, 
#       hex_url,
#       )
#   avrdude_path = 'avrdude'
#   expected_call = "%s -p%s -b%i -c%s -P/dev/tty.usbmodemfa121 -Uflash:w:%s:i" %(avrdude_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
#   expected_call = expected_call.split(' ')
#   got_call = self.uploader.parse_avrdude_command(port, machine, version)
#   #expected_call = expected_call.split(' ')
#   expected_avrdude = expected_call[0]
#   self.assertEqual(expected_avrdude, avrdude_path)
#   for i in range(1, 5):
#     self.assertEqual(expected_call[i], got_call[i])
#   #DO something really hacky, since windows paths have colons in them
#   #and splitting at each colon will result in the test failing on windows
#   #DUMB
#   expected_op = expected_call[-1]
#   expected_op_parts = []
#   expected_op_parts.extend(expected_op[:9].split(':'))
#   expected_op_parts.append(expected_op[10:-2])
#   expected_op_parts.append(expected_op[-1])
#   #Get the path relative from here
#   expected_op_parts[2] = os.path.relpath(expected_op_parts[2])
#   got_op = got_call[-1]
#   got_op_parts = []
#   got_op_parts.extend(expected_op[:9].split(':'))
#   got_op_parts.append(expected_op[10:-2])
#   got_op_parts.append(expected_op[-1])
#   #Get the path relative from here
#   got_op_parts[2] = os.path.relpath(expected_op_parts[2])
#   for i in range(len(expected_op_parts)):
#     self.assertEqual(expected_op_parts[i], got_op_parts[i])

#   def test_update_firmware(self):
#     wget_mock = mock.Mock()
#     self.uploader.wget = wget_mock
#     with open(os.path.join(
#         self.uploader.base_path,
#         'products.json',
#         )) as f:
#       self.uploader.products = json.load(f)
#     
#     check_call_mock = mock.Mock()
#     self.uploader.run_subprocess = check_call_mock
#     port = '/dev/tty.usbmodemfa121'
#     machine = 'Example'
#     version = '0.1'
#     import pdb
#     pdb.set_trace()
#     expected_call = self.uploader.parse_avrdude_command(port, machine, version)
#     self.uploader.upload_firmware(port, machine, version)
#     check_call_mock.assert_called_once_with(expected_call)

if __name__ == "__main__":
  unittest.main()
