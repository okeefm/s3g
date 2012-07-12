import json
import os
import subprocess
from errors import *

class Uploader(object):

  def __init__(self):
    self.conf_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'avrdude.conf')

  def get_machine_board_profile(self, machine):
    extension = '.json'
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'machine_board_profiles', machine+extension)
    with open(path) as f:
      values = json.load(f)
    return values

  def list_versions(self, machine):
    values = self.get_machine_board_profile(machine)
    versions = []
    for version in values['versions']:
      versions.append(version)
    return versions

  def list_machines(self):
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
    call = self.parse_command(port, machine, version)
    subprocess.check_call(call)
