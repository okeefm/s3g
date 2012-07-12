import json
import os
import subprocess
from errors import *

class Uploader(object):

  def __init__(self):
    self.conf_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'avrdude.conf')

  def get_machine_board_profile(self, machine):
    """
    Given a machine name, retrieves the associated .json file and parsed
    out its values.
    TODO: Replace this with a profile object from ../, but that requires
      a profile refactor to take an absolute path
  
    @param str machine: The machine we want information about
    @return dict values: The values parsed out of the machine board profile
    """
    extension = '.json'
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'machine_board_profiles', machine+extension)
    with open(path) as f:
      values = json.load(f)
    return values

  def list_versions(self, machine):
    """
    Given a machine name, returns all possible versions we can upload to

    @param str machine: The machine we want information about
    @return list versions: The versions we can upload
    """
    values = self.get_machine_board_profile(machine)
    versions = []
    for version in values['versions']:
      versions.append(version)
    return versions

  def list_machines(self):
    """
    Lists all the machines we can upload firmware to

    @return list machines: The machines we can upload firmware to
    """
    profile_ext = '.json'
    files = os.listdir(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'machine_board_profiles'))
    machines = []
    for f in files:
      name, ext = os.path.splitext(f)
      if ext == profile_ext:
        machines.append(name)
    return machines
   
  def parse_command(self, port, machine, version):
    """
    Given a port, machine name and version number parses out a command that invokes avrdude

    @param str port: The port the machine is connected to
    @param str machine: The machine we are uploading to
    @param str version: The version of firmware we want to upload to
    @return str command: The command that invokes avrdude
    """
    values = self.get_machine_board_profile(machine)
    try:
      hex_file = str(values['versions'][version])
    except KeyError:
      raise UnknownVersionError
    hex_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'machine_board_profiles', hex_file)
    process = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'avrdude')
    flags = []
    #get the part
    flags.append('-p'+str(values['part']))
    #get the baudrate
    flags.append('-b'+str(values['baudrate']))
    #get the config
    flags.append('-C'+self.conf_path)
    #get the programmer
    flags.append('-c'+str(values['programmer']))
    #get the port
    flags.append('-P'+port)
    #get the operation
    flags.append('-U'+'flash:w:'+hex_file_path+':i')
    return [process] + flags

  def upload(self, port, machine, version):
    """
    Given a port, machine name and version number, invokes avrdude to upload a specific firmware
    version to a specific type of machine.

    @param str port: The port the machine is connected to
    @param str machine: The machine we are uploading to
    @param str version: The version of firmware we want to upload to
    """
    call = self.parse_command(port, machine, version)
    subprocess.check_call(call)
