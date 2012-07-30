import json
import os
import subprocess
import urllib2
from errors import *
import logging

class Uploader(object):

  def __init__(self):
    self._logger = logging.getLogger(self.__class__.__name__)
    self.product_url = './products.json'
    self.base_url = 'http://firmware.makerbot.com'
    #The base path is included for testing purposes.  Without it, we would
    #rely on mock too much
    self.base_path = os.path.abspath(os.path.dirname(__file__))
    #Again, for testing purposes we save this function
    self.check_call = subprocess.check_call
    self.urlopen = urllib2.urlopen

  def update(self):
    """
    Update should be called before any firmware loading
    is done, to ensure the most up-to-date information 
    is being used.
    """
    self.get_products()
    self._logger.info('{"event":"updating_updater"}')

  def get_products(self):
    """
    Pulls the most recent products.json file and, using that,
    pulls all possible machine json files.
    """
    product_url = self.build_firmware_url(self.product_url)
    self.wget_this(product_url)
    #Assuming wget works, this shouldnt be a problem
    self.products = self.load_json_values(os.path.join(self.base_path, 'products.json'))
    self.get_machine_json_files()

  def get_machine_json_files(self):
    """
    Assuming a product.json file has been pulled and loaded, 
    explores that products.json file and wgets all machine json files.
    """
    machines = self.products['ExtrusionPrinters']
    for machine in machines:
      f = self.products['ExtrusionPrinters'][machine]
      url = self.build_firmware_url(self.products['ExtrusionPrinters'][machine])
      self.wget_this(url)

  def wget_this(self, url):
    """
    Given a url, creates a wget call with it and 
    executes wget on it.

    @param str url: The url we want to wget
    """
    self._logger.info('{"event":"downloading_url", "url":%s}' %(url))
    dl_file = self.urlopen(url)
    filename = url.split('/')[-1]
    with open(os.path.join(self.base_path, filename), 'w') as f:
      f.write(dl_file.read())

  def load_json_values(self, path):
    with open(path) as f:
      return json.load(f)

  def build_firmware_url(self, url):
    """Given a url concatenat are return the url 
    onto the base url.

    @param str url: The url we want to access
    @return str full_url: The full url we want to access
    return self.base_url + url
    """
    #If there is a path divider already in place
    if '/' == url[0] or './' == url[:2]:
      return_url = self.base_url + url
    else:
      return_url = self.base_url + '/' + url
    return return_url

  def get_firmware_values(self, machine):
    """
    Given a machine name, retrieves the associated .json file and parses
    out its values.
  
    @param str machine: The machine we want information about
    @return dict values: The values parsed out of the machine board profile
    """
    path = os.path.join(
        self.base_path,
        self.products['ExtrusionPrinters'][machine],
        )
    return self.load_json_values(path)

  def list_firmware_versions(self, machine):
    """
    Given a machine name, returns all possible versions we can upload to

    @param str machine: The machine we want information about
    @return list versions: The versions we can upload
    """
    values = self.get_firmware_values(machine)
    versions = []
    for version in values['firmware']['versions']:
      descriptor = values['firmware']['versions'][version][1]
      versions.append([version, descriptor])
    return versions

  def list_machines(self):
    """
    Lists all the machines we can upload firmware to

    @return iterator machines: The machines we can upload firmware to
    """
    return self.products['ExtrusionPrinters'].keys()

  def parse_avrdude_command(self, port, machine, version):
    """
    Given a port, machine name and version number parses out a command that invokes avrdude

    @param str port: The port the machine is connected to
    @param str machine: The machine we are uploading to
    @param str version: The version of firmware we want to upload to
    @return str command: The command that invokes avrdude
    """
    values = self.get_firmware_values(machine)
    values = values['firmware']
    try:
      hex_file = str(values['versions'][version][0])
    except KeyError:
      raise UnknownVersionError
    hex_file_url = self.build_firmware_url(hex_file)
    #Pull the hex file
    self.wget_this(hex_file_url)
    #Get the path to the hex file
    hex_file_path = hex_file.split('/')[-1]
    hex_file_path = os.path.join(self.base_path, hex_file_path)
    process = 'avrdude'
    flags = []
    #get the part
    flags.append('-p'+str(values['part']))
    #get the baudrate
    flags.append('-b'+str(values['baudrate']))
    #get the programmer
    flags.append('-c'+str(values['programmer']))
    #get the port
    flags.append('-P'+port)
    #get the operation
    flags.append('-U'+'flash:w:'+hex_file_path+':i')
    return [process] + flags

  def upload_firmware(self, port, machine, version):
    """
    Given a port, machine name and version number, invokes avrdude to upload a specific firmware
    version to a specific type of machine.

    @param str port: The port the machine is connected to
    @param str machine: The machine we are uploading to
    @param str version: The version of firmware we want to upload to
    """
    self._logger.info('{"event":"uploading_firmware", "port":%s, "machine":%s, "version":%s}' %(port, machine, version))
    call = self.parse_avrdude_command(port, machine, version)
    self.check_call(call)
