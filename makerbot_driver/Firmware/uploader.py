import json
import os
import subprocess
import urllib2
from errors import *
import logging    
import urlparse


class Uploader(object):
  """ Firmware Uploader is used to send firmware to a 3D printer."""
  
  def __init__(self, source_url = None, dest_path = None, autoUpdate= True):
    """Build an uploader.
	@param source_url: specify a url to fetch firmware metadata from. Can be a directory
    @param dest_path: path to use as the local file store location
    @param autoUpdate: automatically and immedately fetch machine data
    """
    self._logger = logging.getLogger(self.__class__.__name__)
    self.product_filename = 'products.json'
    self.source_url = source_url if source_url else 'http://firmware.makerbot.com'
    self.dest_path = dest_path if dest_path else os.getcwd()
    
    self.run_subprocess = subprocess.check_call
    self.urlopen = urllib2.urlopen
    if autoUpdate:
        self.update()

  def pathjoin(self, base, resource):
    """ joins URL or filename paths to find a resource relative to base"""
    if( base.startswith('http://')):
        return urlparse.urljoin(base, resource)
    return os.path.normpath(os.path.join(base, resource))

  def update(self):
    """
    Update should be called before any firmware loading is done, to ensure the
    most up-to-date information is being used.
    """
    self._logger.info('{"event":"updating_updater"}')
    self._pull_products()


  def _pull_products(self):
    """
    Pulls the most recent products.json file and, using that
    to update internal manchine lists and metadata
    """
    product_filename = self.pathjoin(self.source_url, self.product_filename)
    filename = self.wget(product_filename)
    #Assuming wget works, this shouldnt be a problem
    self.products = self.load_json_values(filename)
    self.get_machine_json_files()

  def get_machine_json_files(self):
    """
    Assuming a product.json file has been pulled and loaded, 
    explores that products.json file and wgets all machine json files.
    """
    machines = self.products['ExtrusionPrinters']
    for machine in machines:
      f = self.products['ExtrusionPrinters'][machine]
      url = self.pathjoin(self.source_url,  self.products['ExtrusionPrinters'][machine])
      self.wget(url)

  def wget(self, url):
    """
    Gets a certain file from a url and copies it into 
    the current working directory.  If the url is stored
    locally, we copy that file.  Otherwise we pull it from
    the internets.

    @param str url: The url we want to wget
    @return file: local filename of the resource
    """
    filename = url.split('/')[-1] #urllib here might be useful
    filename = os.path.join(self.dest_path, filename) 
    #If file is local
    if os.path.isfile(url):
      import shutil
	  if os.path.samefile(url, filename):
		return filename #someone silly is copying files overthemselves
      shutil.copy(url, filename)
      return filename
    else:
      self._logger.info('{"event":"downloading_url", "url":%s}' %(url))
      #Download the file
      dl_file = self.urlopen(url)
      #Write out the file
      with open(filename, 'w') as f:
        f.write(dl_file.read())
      return filename 
    
  def load_json_values(self, path):
    with open(path) as f:
      return json.load(f)

  def get_firmware_values(self, machine):
    """
    Given a machine name, retrieves the associated .json file and parses
    out its values.
  
    @param str machine: The machine we want information about
    @return dict values: The values parsed out of the machine board profile
    """
    path = os.path.join(
        self.dest_path,
        self.products['ExtrusionPrinters'][machine],
        )
    path = os.path.normpath(path)
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
    hex_file_url = self.pathjoin(self.source_url, hex_file)
    hex_file_path = self.wget(hex_file_url)
    #Get the path to the hex file
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
    self.run_subprocess(call)
