import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import json
import mock

import s3g

class TestGetProducts(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.wget_this_mock = mock.Mock()
    self.get_machine_json_files_mock = mock.Mock()
    self.uploader.wget_this = self.wget_this_mock
    self.uploader.get_machine_json_files = self.get_machine_json_files_mock 
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.uploader.base_path = base_path

  def tearDown(self):
    self.uploader = None

  def test_get_products(self):
    self.uploader.get_products()
    expected_products_url = self.uploader.build_firmware_url('./products.json')
    self.wget_this_mock.assert_called_once_with(expected_products_url)
    self.get_machine_json_files_mock.assert_called_once_with() 

class TestWgetThis(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.check_call_mock = mock.Mock()
    self.uploader.check_call = self.check_call_mock

  def tearDown(self):
    self.uploader = None

  def test_wget_this(self):
    f = 'firmware.makerbot.com/products.json'
    expected_subprocess_call = self.uploader.make_wget_call(f)
    self.uploader.wget_this(f)
    self.check_call_mock.assert_called_once_with(expected_subprocess_call)

class TestGetMachineJsonFiles(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    self.wget_this_mock = mock.Mock()
    self.uploader.wget_this = self.wget_this_mock

  def tearDown(self):
    self.uploader = None

  def test_get_machine_json_files_no_products(self):
    self.assertRaises(AttributeError, self.uploader.get_machine_json_files)

  def test_get_machine_json_files_products_pulled_and_loaded(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_files', 'products.json')) as f:
      self.uploader.products = json.load(f)
    self.uploader.get_machine_json_files()
    calls = self.wget_this_mock.mock_calls
    machines = self.uploader.products['ExtrusionPrinters']
    for machine, call in zip(machines, calls):
      url = self.uploader.products['ExtrusionPrinters'][machine]
      firmware_url = self.uploader.build_firmware_url(url)
      self.assertEqual(firmware_url, call[1][0])

class TestGetFirmwareVersions(unittest.TestCase):

  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.uploader.base_path = base_path

  def tearDown(self):
    self.uploader = None

  def test_list_firmware_versions_bad_machine_name(self):
    self.assertRaises(
        AttributeError, 
        self.uploader.list_firmware_versions, 
        'I HOPE THIS ISNT A MACHINE NAME'
        )

  def test_list_firmware_versions_good_machine_name(self):
    with open(os.path.join(self.uploader.base_path, 'products.json')) as f:
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
      expected_versions.append(version)
    got_versions = self.uploader.list_firmware_versions(machine)
    self.assertEqual(expected_versions, got_versions)

class TestGetMachineBoardProfile(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.uploader.base_path = base_path
    with open(os.path.join(base_path, 'products.json')) as f:
      self.uploader.products = json.load(f)

  def tearDown(self):
    self.uploader = None

  def test_get_machine_board_profile_bad_machine(self):
    machine = "i really hope you dont have a file with this exact name"
    self.assertRaises(KeyError, self.uploader.get_machine_board_profile, machine)

  def test_get_machine_board_profile_values(self):
    machine = "Example"
    with open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'Example.json'
        )) as f: 
      expected_values = json.load(f)
    self.assertEqual(expected_values, self.uploader.get_machine_board_profile(machine))

class TestListVersions(unittest.TestCase):
  def setUp(self):
    base_path = os.path.abspath(os.path.dirname(__file__))
    self.uploader = s3g.Firmware.Uploader()
    self.uploader.base_path = base_path

  def test_list_machines_no_products(self):
    self.assertRaises(AttributeError, self.uploader.list_machines)

  def test_list_machines(self):
    with open(os.path.join(
        self.uploader.base_path,
        'test_files',
        'products.json',
        )) as f:
      values = json.load(f)
    self.uploader.products = values
    expected_machines = []
    for machine in values['ExtrusionPrinters']:
       expected_machines.append(machine)
    self.assertEqual(expected_machines, self.uploader.list_machines())

class TestUploader(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()

  def tearDown(self):
    self.uploader = None

  def test_build_firmware_url_no_file_separator(self):
    base_url = 'firmware.makerbot.com'
    f = 'products.json'
    expected_url = '%s/%s' %(base_url, f)
    got_url = self.uploader.build_firmware_url(f)
    self.assertEqual(expected_url, got_url)

  def test_build_firmware_url_has_file_separator(self):
    base_url = 'firmware.makerbot.com'
    f = './products.json'
    expected_url = base_url+f
    got_url = self.uploader.build_firmware_url(f)
    self.assertEqual(expected_url, got_url)

  def test_load_json_values_good_file(self):
    path_to_json = os.path.join(os.path.abspath(os.path.dirname(__file__)),'test_files','products.json')
    with open(path_to_json) as f:
      expected_vals = json.load(f)
    got_vals = self.uploader.load_json_values(path_to_json)
    self.assertEqual(expected_vals, got_vals)

  def test_load_json_values_bad_file(self):
    filename = 'I HOPE THIS ISNT A FILENAME'
    self.assertRaises(IOError, self.uploader.load_json_values, filename)

  def test_make_wget_call(self):
    f = 'file.json'
    expected_call = ['wget', '-N', f, '-P%s' % self.uploader.base_path ]
    got_call = self.uploader.make_wget_call(f)
    self.assertEqual(expected_call, got_call)

class TestParseAvrdudeCommand(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()
    base_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.uploader.base_path = base_path
        
  def test_parse_avrdude_command_no_products(self):
    port = '/dev/tty.usbmodemfa121'
    machine = "Example"
    version = '0.1'
    self.assertRaises(AttributeError, self.uploader.parse_avrdude_command, port, machine, version)

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

  def test_parse_avrdude_command(self):
    wget_this_mock = mock.Mock()
    self.uploader.wget_this = wget_this_mock
    with open(os.path.join(
        self.uploader.base_path,
        'products.json',
        )) as f:
      self.uploader.products = json.load(f)
    with open(os.path.join(self.uploader.base_path, 'Example.json')) as f:
      example_profile = json.load(f)
    example_values = example_profile['firmware']
    port = '/dev/tty.usbmodemfa121'
    machine = 'Example'
    version = '0.1'
    hex_url = example_values['versions'][version][0]
    hex_path = os.path.join(
        self.uploader.base_path, 
        hex_url,
        )
    avrdude_path = 'avrdude'
    expected_call = "%s -p%s -b%i -c%s -P/dev/tty.usbmodemfa121 -Uflash:w:%s:i" %(avrdude_path, example_values['part'], example_values['baudrate'], example_values['programmer'], hex_path)
    expected_call = expected_call.split(' ')
    got_call = self.uploader.parse_avrdude_command(port, machine, version)
    #expected_call = expected_call.split(' ')
    expected_avrdude = expected_call[0]
    self.assertEqual(expected_avrdude, avrdude_path)
    for i in range(1, 5):
      self.assertEqual(expected_call[i], got_call[i])
    #DO something really hacky, since windows paths have colons in them
    #and splitting at each colon will result in the test failing on windows
    #DUMB
    expected_op = expected_call[-1]
    expected_op_parts = []
    expected_op_parts.extend(expected_op[:9].split(':'))
    expected_op_parts.append(expected_op[10:-2])
    expected_op_parts.append(expected_op[-1])
    #Get the path relative from here
    expected_op_parts[2] = os.path.relpath(expected_op_parts[2])
    got_op = got_call[-1]
    got_op_parts = []
    got_op_parts.extend(expected_op[:9].split(':'))
    got_op_parts.append(expected_op[10:-2])
    got_op_parts.append(expected_op[-1])
    #Get the path relative from here
    got_op_parts[2] = os.path.relpath(expected_op_parts[2])
    for i in range(len(expected_op_parts)):
      self.assertEqual(expected_op_parts[i], got_op_parts[i])
    wget_this_mock.assert_called_once_with(self.uploader.build_firmware_url(hex_url))

  def test_update_firmware(self):
    wget_this_mock = mock.Mock()
    self.uploader.wget_this = wget_this_mock
    with open(os.path.join(
        self.uploader.base_path,
        'products.json',
        )) as f:
      self.uploader.products = json.load(f)
    check_call_mock = mock.Mock()
    self.uploader.check_call = check_call_mock
    port = '/dev/tty.usbmodemfa121'
    machine = 'Example'
    version = '0.1'
    expected_call = self.uploader.parse_avrdude_command(port, machine, version)
    self.uploader.upload_firmware(port, machine, version)
    check_call_mock.assert_called_once_with(expected_call)

if __name__ == "__main__":
  unittest.main()
