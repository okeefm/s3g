#Gcode parser, 

from states import *
from utils import *
from errors import *
import logging
import time

class GcodeParser(object):
  """
  Read in gcode line by line, tracking some state variables and running known
  commands against an s3g machine.
  """
  def __init__(self):
    self.state = GcodeStates()
    self.s3g = None
    self.environment = {}
    self.line_number = 1
    self._log = logging.getLogger(self.__class__.__name__)

    # Note: The datastructure looks like this:
    # [0] : command name
    # [1] : allowed codes
    # [2] : allowed flags

    self.GCODE_INSTRUCTIONS = {
      1   : [self.LinearInterpolation,         'XYZABEF', ''],
      4   : [self.Dwell,                       'P',       ''],
      10  : [self.StoreOffsets,                'XYZP',    ''],
      54  : [self.UseP1Offsets,                '',        ''],
      55  : [self.UseP2Offsets,                '',        ''],
      92  : [self.SetPosition,                 'XYZABE',  ''],
      130 : [self.SetPotentiometerValues,      'XYZAB',   ''],
      161 : [self.FindAxesMinimums,            'F',       'XYZ'],
      162 : [self.FindAxesMaximums,            'F',       'XYZ'],
}

    self.MCODE_INSTRUCTIONS = {
       18  : [self.DisableAxes,                '',        'XYZAB'],
       70  : [self.DisplayMessage,             'P',       ''],
       72  : [self.PlaySong,                   'P',       ''],
       73  : [self.SetBuildPercentage,         'P',       ''],
       101 : [self.ExtruderOnForward,          '',        ''], #This command is explicitely ignored
       102 : [self.ExtruderOnReverse,          '',        ''], #This command is explicitely ignored
       103 : [self.ExtruderOff,                'T',       ''],       #This command is explicitely ignored
       104 : [self.SetToolheadTemperature,     'ST',      ''],
       105 : [self.GetTemperature,             '',        ''],
       109 : [self.SetPlatformTemperature,     'ST',      ''],
       126 : [self.EnableExtraOutput,          'T',       ''],
       127 : [self.DisableExtraOutput,         'T',       ''],
       132 : [self.LoadPosition,               '',        'XYZAB'],
       133 : [self.WaitForToolReady,           'PT',      ''],
       134 : [self.WaitForPlatformReady,       'PT',      ''],
       135 : [self.ChangeTool,                 'T',       ''],
    }

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """
    #If command is in unicode, encode it into ascii
    if isinstance(command, unicode):
      self._log.warning('{"event":"encoding_gcode_into_utf8"}\n')
      command = command.encode("utf8")
    elif not isinstance(command, str):
      self._log.error('{"event":"gcode_file_in_improper_format"}\n')
      raise ImproperGcodeEncodingError

    try:
      command = VariableSubstitute(command, self.environment) 

      codes, flags, comment = ParseLine(command)

      if 'G' in codes:
        if codes['G'] in self.GCODE_INSTRUCTIONS:
          CheckForExtraneousCodes(codes.keys(), self.GCODE_INSTRUCTIONS[codes['G']][1])
          CheckForExtraneousCodes(flags, self.GCODE_INSTRUCTIONS[codes['G']][2])
          self.GCODE_INSTRUCTIONS[codes['G']][0](codes, flags, comment)

        else:
          self._log.error('{"event":"unrecognized_command", "command":%s}\n'
              %(codes['G']))
          gcode_error = UnrecognizedCommandError()
          gcode_error.values['UnrecognizedCommand'] = codes['G']
          raise gcode_error

      elif 'M' in codes:
        if codes['M'] in self.MCODE_INSTRUCTIONS:
          CheckForExtraneousCodes(codes.keys(), self.MCODE_INSTRUCTIONS[codes['M']][1])
          CheckForExtraneousCodes(flags, self.MCODE_INSTRUCTIONS[codes['M']][2])
          self.MCODE_INSTRUCTIONS[codes['M']][0](codes, flags, comment)

        else:
          self._log.error('{"event":"unrecognized_command", "command":%s}\n'
              %(codes['M']))
          gcode_error = UnrecognizedCommandError()
          gcode_error.values['UnrecognizedCommand'] = codes['M']
          raise gcode_error

      # Not a G or M code, should we throw here?
      else:
        if len(codes) + len(flags) > 0:
          self._log.error('{"event":"extraneous_code"}\n')
          gcode_error = ExtraneousCodeError()
          raise gcode_error

        else:
          pass
    except KeyError as e:
      if e[0] == 'T':
        self._log.warning('{"event":"t_code_not_defined"}\n')
        TCodeNotDefinedWarning()
      else:
        self._log.error('{"event":"missing_code_error", "missing_code":%s}\n'
            %(e[0]))
        gcode_error = MissingCodeError()
        gcode_error.values['MissingCode'] = e[0]
        gcode_error.values['LineNumber'] = self.line_number
        gcode_error.values['Command'] = command
        raise gcode_error
    except VectorLengthZeroError:
      self._log.warning('{"event":vector_length_zero_error"}\n')
      pass
    except GcodeError as gcode_error:
      self._log.error('{"event":"gcode_error"}\n')
      gcode_error.values['Command'] = command
      gcode_error.values['LineNumber'] = self.line_number
      raise gcode_error
    self.line_number += 1

  def SetPotentiometerValues(self, codes, flags, comment):
    """Given a set of codes, sets the machine's potentiometer value to a specified value in the codes

    @param dict codes: Codes parsed out of the gcode command
    """
    #Put all values in a hash table
    valTable = {}
    #For each code in codes thats an axis:
    for a in ParseOutAxes(codes):
      #Try to append it to the appropriate list
      try:
        valTable[codes[a]].append(a)
      #Never been encountered before, make a list
      except KeyError:
        valTable[codes[a]] = [a]
    for val in valTable:
      self.s3g.SetPotentiometerValue(valTable[val], val)

  def FindAxesMaximums(self, codes, flags, command):
    """Moves the given axes in the position direction until a timeout
    or endstop is reached
    This function loses the state machine's position.
    """
    axes = ParseOutAxes(flags)
    if len(axes) == 0:
      return
    self.state.LosePosition(flags)
    #We need some axis information to calc the DDA speed
    axes_feedrates, axes_SPM = self.state.GetAxesFeedrateAndSPM(axes)
    dda_speed = CalculateHomingDDASpeed(
        codes['F'], 
        axes_feedrates,
        axes_SPM
        )
    self.s3g.FindAxesMaximums(axes, dda_speed, self.state.profile.values['find_axis_maximum_timeout'])

  def FindAxesMinimums(self, codes, flags, comment):
    """Moves the given axes in the negative direction until a timeout
    or endstop is reached.
    This function loses the state machine's position.
    """
    axes = ParseOutAxes(flags)
    if len(axes) == 0:
      return
    self.state.LosePosition(flags) 
    #We need some axis information to calc the DDA speed
    axes_feedrates, axes_SPM = self.state.GetAxesFeedrateAndSPM(axes)
    dda_speed = CalculateHomingDDASpeed(
        codes['F'], 
        axes_feedrates,
        axes_SPM
        )
    self.s3g.FindAxesMinimums(axes, dda_speed, self.state.profile.values['find_axis_minimum_timeout'])

  def SetPosition(self, codes, flags, comment):
    """Explicitely sets the position of the state machine and bot
    to the given point
    """
    self.state.SetPosition(codes)
    stepped_position = MultiplyVector(self.state.GetPosition(), self.state.GetAxesValues('steps_per_mm'))
    self.s3g.SetExtendedPosition(stepped_position)
      
  def UseP1Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P0 offset.
    """
    self.state.offset_register = 1
    self._log.info('{"event":"gcode_state_change", "change":"offset_register", "new_offset_register": %i}\n'
        %(self.state.offset_register))

  def UseP2Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P1 offset.
    """
    self.state.offset_register = 2
    self._log.info('{"event":"gcode_state_change", "change":"offset_register", "new_offset_register": %i}\n'
        %(self.state.offset_register))

  def WaitForToolReady(self, codes, flags, comment):
    """
    Waits for a toolhead for some amount of time.  If either of 
    these codes are not defined (T and P respectively), the 
    default values in the gcode state is used.
    """
    if 'P' in codes:
      timeout = codes['P']
    else:
      timeout = self.state.wait_for_ready_timeout

    self.s3g.WaitForToolReady(
        codes['T'],
        self.state.wait_for_ready_packet_delay,
        timeout
        )

  def WaitForPlatformReady(self, codes, flags, comment):
    """
    Waits for a platform for some amount of time.  If either
    of these codes are not defined (T and P respectively), the
    default vaules in the gcode state is used.
    """
    if 'P' in codes:
      timeout = codes['P']
    else:
      timeout = self.state.wait_for_ready_timeout
    self.s3g.WaitForPlatformReady(
        codes['T'],
        self.state.wait_for_ready_packet_delay,
        timeout
        )

  def DisableAxes(self, codes, flags, comment):
    """Disables a set of axes on the bot
    """
    self.s3g.ToggleAxes(ParseOutAxes(flags), False)

  def DisplayMessage(self, codes, flags, comment):
    """Given a comment, displays a message on the bot.
    """
    row = 0 # As per the gcode protocol
    col = 0 # As per the gcode protocol
    clear_existing = False #If false, clears the message buffer
    last_in_group = True #If true, signifies this is the last in a group
    wait_for_button = False #If true, signifies a button wait

    self.s3g.DisplayMessage(
        row,
        col,
        comment,
        codes['P'],
        clear_existing,
        last_in_group,
        wait_for_button,
      )

  def PlaySong(self, codes, flags, comment):
    """Plays a song as a certain register on the bot.
    """
    self.s3g.QueueSong(codes['P'])

  def SetBuildPercentage(self, codes, flags, comment):
    """Sets the build percentage to a certain percentage.
    """
    percentage = codes['P']

    if percentage > 100 or percentage < 0:
      raise BadPercentageError

    self.s3g.SetBuildPercent(percentage)

    # Side effect: If the build percentage is 0 or 100, then also send a build start or build end notification.
    # TODO: Should this be called first? is order of operations important?
    if 0 == percentage:
      self.BuildStartNotification()

    elif 100 == percentage:
      self.BuildEndNotification()

  def StoreOffsets(self, codes, flags, comment):
    """Given XYZ offsets and an offset index, stores those 
    offsets in the state machine.
    """
    self.state.offsetPosition[codes['P']].SetPoint(codes)

  def LinearInterpolation(self, codes, flags, comment):
    """Movement command that has two flavors: E and AB commands.
    E Commands require a preset toolhead to use, and simply increment
    that toolhead's coordinate.
    AB Commands increment the AB axes.
    Having both E and A or B codes will throw errors.
    """
    if 'F' in codes:
      self.state.values['feedrate'] = codes['F']
      self._log.info('{"event":"gcode_state_change", "change":"store_feedrate", "new_feedrate":%i}\n'
          %(codes['F']))
    if len(ParseOutAxes(codes)) > 0 or 'E' in codes:
      if 'A' in codes and 'B' in codes:
        gcode_error = ConflictingCodesError()
        gcode_error.values['ConflictingCodes'] = ['A', 'B']
        raise gcode_error
      current_position = self.state.GetPosition()
      self.state.SetPosition(codes)
      try :
        feedrate = self.state.values['feedrate']
        dda_speed = CalculateDDASpeed(
            current_position, 
            self.state.GetPosition(), 
            feedrate,
            self.state.GetAxesValues('max_feedrate'),
            self.state.GetAxesValues('steps_per_mm'),
            )
        stepped_point = MultiplyVector(
            self.state.GetPosition(), 
            self.state.GetAxesValues('steps_per_mm')
            )
        self.s3g.QueueExtendedPoint(stepped_point, dda_speed)

      except KeyError as e:
        if e[0] == 'feedrate': # A key error would return 'feedrate' as the missing key,
                             # when in respect to the executed command the 'F' command
                             # is the one missing. So we remake the KeyError to report
                             # 'F' instead of 'feedrate'.
          e = KeyError('F')
        raise e

  def Dwell(self, codes, flags, comment):
    """Pauses the machine for a specified amount of miliseconds
    Because s3g takes in microseconds, we convert miliseconds into
    microseconds and send it off.
    """
    microConstant = 1000000
    miliConstant = 1000
    d = codes['P'] * microConstant/miliConstant
    self.s3g.Delay(d)

  def SetToolheadTemperature(self, codes, flags, comment):
    """Sets the toolhead temperature for a specific toolhead to
    a specific temperature.  We set the state's tool_idnex to be the
    'T' code (if present) and use that tool_index when heating.
    """
    self.s3g.SetToolheadTemperature(codes['T'], codes['S'])

  def SetPlatformTemperature(self, codes, flags, comment):
    """Sets the platform temperature for a specific toolhead to a specific 
    temperature.  We set the state's tool_index to be the 'T' code (if present)
    and use that tool_index when heating.
    """
    self.s3g.SetPlatformTemperature(codes['T'], codes['S'])

  def LoadPosition(self, codes, flags, comment):
    """Loads the home positions for the XYZ axes from the eeprom
    """
    axes = ParseOutAxes(flags)
    self.state.LosePosition(axes)
    self.s3g.RecallHomePositions(axes)

  def ChangeTool(self, codes, flags, comments):
    """Sends a chagne tool command to the machine.
    """
    self.state.values['tool_index'] = codes['T']
    self._log.info('{"event":"gcode_state_change", "change":"tool_change", "new_tool_index":%i}\n'
        %(codes['T']))
    self.s3g.ChangeTool(codes['T'])

  def BuildStartNotification(self):
    """Sends a build start notification command to the machine.
    """
    self._log.info('{"event":"build_start"}\n')
    try:
      self.s3g.BuildStartNotification(self.state.values['build_name'])
    except KeyError:
      self._log.info('{"event":"no_build_name_defined"}\n')
      raise NoBuildNameError

  def BuildEndNotification(self):
    """Sends a build end notification command to the machine
    """
    self._log.info('{"event":"build_end"}\n')
    self.state.values['build_name'] = None
    self._log.info('{"event":"gcode_state_change", "change":"remove_build_name"}\n')
    self.s3g.BuildEndNotification()

  def EnableExtraOutput(self, codes, flags, comment):
    """
    Enables an extra output attached to a certain toolhead
    of the machine
    """
    self.s3g.ToggleExtraOutput(codes['T'], True)

  def DisableExtraOutput(self, codes, flags, comment):
    """
    Disables an extra output attached to a certain toolhead
    of the machine
    """
    self.s3g.ToggleExtraOutput(codes['T'], False)

  def ExtruderOff(self, codes, flags, comment):
    """Turn the extruder off
    This is a stub, since we dropped support for this function
    """
    self._log.warning('{"event":"passing_over_code", "code":103}\n')

  def ExtruderOnReverse(self, codes, flags, comment):
    """Turn the extruder on turning backward
    This is a stub, since we dropped support for this function
    """
    self._log.warning('{"event":"passing_over_code", "code":102}\n')

  def ExtruderOnForward(self, codes, flags, comment):
    """Turn the extruder on turning forward
    This is a stub, since we dropped support for this function
    """
    self._log.warning('{"event":"passing_over_code", "code":101}\n')

  def GetTemperature(self, codes, flags, comment):
    """This gets the temperature from a toolhead
    We do not support this command, and only have a stub because
    skeinforge likes to include it in its files
    """
    self._log.warning('{"event":"passing_over_code", "code":105}\n')
