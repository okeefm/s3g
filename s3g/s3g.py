# Some utilities for speaking s3g
import struct
import time

# TODO: Do these go in their own namespace?
from constants import *
from errors import *
from crc import *
from coding import *
from packet import *
import logging

class s3g(object):
  def __init__(self):
    self.file = None
    #self.logfile = open('output_stats','w')
    self.logger = logging.getLogger('output_stats')
    hdlr = logging.FileHandler('./output_stats')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    self.logger.addHandler(hdlr)
    self.logger.setLevel(logging.ERROR)
    self.ExtendedPointLength = 5
    self.PointLength = 3

    self.total_retries = 0
    self.total_overflows = 0

  def BuildAndSendPayload(self, *args):
    """
    Given a set of parameters, puts them into a bytearray and send them off using SendCommand

    @param *args A set of arguments to put inside a bytearray
    """
    payload = bytearray()
    AddObjToPayload(payload, args)
    return self.SendCommand(payload)

  def SendCommand(self, payload):
    """
    Wraps a payload in a packet with a header, length, payload and proper CRC to send to the machine
    @param payload Command to send to the machine
    @return Response payload, if successful. 
    """
    packet = EncodePayload(payload)
    return self.SendPacket(packet)


  def SendPacket(self, packet):
    """
    Attempt to send a packet to the machine, retrying up to 5 times if an error
    occurs.
    @param packet Packet to send to the machine
    @return Response payload, if successful. 
    """
    overflow_count = 0
    retry_count = 0

    while True:
      decoder = PacketStreamDecoder()
      self.file.write(packet)
      self.file.flush()

      # Timeout if a response is not received within 1 second.
      start_time = time.time()

      try:
        while (decoder.state != 'PAYLOAD_READY'):
          # Try to read a byte
          data = ''
          while data == '':
            if (time.time() > start_time + timeout_length):
              raise TimeoutError(len(data), decoder.state)

            # pySerial streams handle blocking read. Be sure to set up a timeout when
            # initializing them, or this could hang forever
            data = self.file.read(1)

          data = ord(data)
          decoder.ParseByte(data)
       
        CheckResponseCode(decoder.payload[0])        
 
        # TODO: Should we chop the response code?
        return decoder.payload

      except (BufferOverflowError) as e:
        # Buffer overflow error- wait a while for the buffer to clear, then try again.
        # TODO: This could hang forever if the machine gets stuck; is that what we want?

        self.logger.warning('{"event":"buffer_overflow", "overflow_count":%i, "retry_count"=%i}\n'
          %(overflow_count,retry_count))

        self.total_overflows += 1
        overflow_count += 1

        time.sleep(.2)

      except (PacketDecodeError, RetryError, TimeoutError) as e:
        # Sent a packet to the host, but got a malformed response or timed out waiting
        # for a reply. Retry immediately.

        self.logger.warning('{"event":"transmission_problem", "exception":"%s", "message":"%s" "retry_count"=%i}\n'
          %(type(e),e.__str__(),retry_count))

        self.total_retries += 1
        retry_count += 1

      except Exception as e:
        # Other exceptions are propigated upwards.

        self.logger.warning('{"event":"unhandled_exception", "exception":"%s", "message":"%s" "retry_count"=%i}\n'
          %(type(e),e.__str__(),retry_count))
        raise e

      if retry_count >= max_retry_count:
        self.logger.warning('{"event":"transmission_error"}\n')
        raise TransmissionError


  def GetVersion(self):
    """
    Get the firmware version number of the connected machine
    @return Version number
    """
    response = self.BuildAndSendPayload(
      host_query_command_dict['GET_VERSION'], 
      EncodeUint16(s3g_version)
    )
    [response_code, version] = UnpackResponse('<BH', response)

    return version

  def CaptureToFile(self, filename):
    """
    Capture all subsequent commands up to the 'end capture' command to a file with the given filename on an SD card.
    @param str filename: The name of the file to write to on the SD card
    """
    response = self.BuildAndSendPayload(
      host_query_command_dict['CAPTURE_TO_FILE'], 
      filename, 
      0x00
    )
    [response_code, sd_response_code] = UnpackResponse('<BB', response)
    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

  def EndCaptureToFile(self):
    """
    Send the end capture signal to the bot, so it stops capturing data and writes all commands out to a file on the SD card
    @return The number of bytes written to file
    """
    response = self.BuildAndSendPayload(host_query_command_dict['END_CAPTURE'])
    
    [response_code, sdResponse] = UnpackResponse('<BI', response)
    return sdResponse

  def Reset(self):
    """
    Reset the bot, unless the bot is waiting to tell us a build is cancelled.
    """
    self.BuildAndSendPayload(host_query_command_dict['RESET'])


  def IsFinished(self):
    """
    Checks if the steppers are still executing a command
    """
    response = self.BuildAndSendPayload(host_query_command_dict['IS_FINISHED'])
    
    [response_code, isFinished] = UnpackResponse('<B?', response)
    return isFinished

  def ClearBuffer(self):
    """
    Clears the buffer of all commands
    """
    self.BuildAndSendPayload(host_query_command_dict['CLEAR_BUFFER'])

  def Pause(self):
    """
    Pause the machine
    """
    self.BuildAndSendPayload(host_query_command_dict['PAUSE'])

  def GetCommunicationStats(self):
    """
    Get some communication statistics about traffic on the tool network from the Host.
    """
    response = self.BuildAndSendPayload(host_query_command_dict['GET_COMMUNICATION_STATS'])

    [response_code,
     packetsReceived,
     packetsSent,
     nonResponsivePacketsSent,
     packetRetries,
     noiseBytes] = UnpackResponse('<BLLLLL', response)

    info = {
    'PacketsReceived' : packetsReceived,
    'PacketsSent' : packetsSent,
    'NonResponsivePacketsSent' : nonResponsivePacketsSent,
    'PacketRetries' : packetRetries,
    'NoiseBytes' : noiseBytes,
    }
    return info

  def GetMotherboardStatus(self):
    """
    Retrieve bits of information about the motherboard
    @return: A python dictionary of various flags and whether theywere set or not at reset
    POWER_ERRPR : An error was detected with the system power.
    """
    response = self.BuildAndSendPayload(host_query_command_dict['GET_MOTHERBOARD_STATUS'])
    

    [response_code, bitfield] = UnpackResponse('<BB', response)

    bitfield = DecodeBitfield8(bitfield)      

    flags = {
    'POWER_ERROR' : int(bitfield[7]),
    }
    return flags

  def ExtendedStop(self, halt_steppers, clear_buffer):
    """
    Stop the stepper motor motion and/or reset the command buffer.  This differs from the 
    reset and abort commands in that a soft reset of all functions isnt called.
    @param boolean halt_steppers: A flag that if true will stop the steppers
    @param boolean clear_buffer: A flag that, if true, will clear the buffer
    """
    bitfield = 0
    if halt_steppers:
      bitfield |= 0x01
    if clear_buffer:
      bitfield |= 0x02
    response = self.BuildAndSendPayload(
      host_query_command_dict['EXTENDED_STOP'],  
      bitfield
    )

    [response_code, extended_stop_response] = UnpackResponse('<BB', response)
    # TODO: can this be anything besides 1?
    if extended_stop_response == 1:
      raise ExtendedStopError

  def WaitForPlatformReady(self, tool_index, delay, timeout):
    """
    Halts the machine until the specified toolhead reaches a ready state, or if the
    timeout is reached.  Toolhead is ready if its temperature is within a specified
    range.
    @param int tool_index: toolhead index
    @param int delay: Time in ms between packets to query the toolhead
    @param int timeout: Time to wait in seconds for the toolhead to heat up before moving on
    """
    self.BuildAndSendPayload(
      host_action_command_dict['WAIT_FOR_PLATFORM_READY'], 
      tool_index, 
      EncodeUint16(delay), 
      EncodeUint16(timeout)
    )
    
  def WaitForToolReady(self, tool_index, delay, timeout):
    """
    Halts the machine until the specified toolhead reaches a ready state, or if the
    timeout is reached.  Toolhead is ready if its temperature is within a specified
    range.
    @param int tool_index: toolhead index
    @param int delay: Time in ms between packets to query the toolhead
    @param int timeout: Time to wait in seconds for the toolhead to heat up before moving on
    """
    self.BuildAndSendPayload(
      host_action_command_dict['WAIT_FOR_TOOL_READY'], 
      tool_index, 
      EncodeUint16(delay), 
      EncodeUint16(timeout)
    )

  def Delay(self, delay):
    """
    Halts all motion for the specified amount of time
    @param int delay: Delay time, in microseconds
    """
    self.BuildAndSendPayload(
      host_action_command_dict['DELAY'], 
      EncodeUint32(delay)
    )

  def ToggleAxes(self, axes, enable):
    """
    Used to explicitly power steppers on or off.
    @param list axes: Array of axis names ['x', 'y', ...] to configure
    @param boolean enable: If true, enable all selected axes. Otherwise, disable the selected
           axes.
    """
    axes_bitfield = EncodeAxes(axes)
    if enable:
      axes_bitfield |= 0x80
    self.BuildAndSendPayload(
      host_action_command_dict['ENABLE_AXES'], 
      axes_bitfield
    )


  def QueueExtendedPointNew(self, point, duration, relative_axes):
    """
    Queue a point with the new style!  Moves to a certain point over a given duration
    with either relative or absolute positioning.  Relative vs. Absolute positioning
    is done on an axis to axis basis.

    @param list point: A 5 dimentional point in steps specifying where each axis should move to
    @param int duration: The total duration of the move in miliseconds
    @param list relative_axes: Array of axes whose coordinates should be considered relative
    """
    if len(point) != self.ExtendedPointLength:
      raise PointLengthError(len(point))

    self.BuildAndSendPayload(
      host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'], 
      [EncodeInt32(cor) for cor in point], 
      EncodeUint32(duration), 
      EncodeAxes(relative_axes)
    )
  
  def StoreHomePositions(self, axes):
    """
    Write the current axes locations to the EEPROM as the home position
    @param list axes: Array of axis names ['x', 'y', ...] whose position should be saved
    """
    self.BuildAndSendPayload(
      host_action_command_dict['STORE_HOME_POSITIONS'], 
      EncodeAxes(axes)
    )

  def SetPotentiometerValue(self, axes, value):
    """
    Sets the value of the digital potentiometers that control the voltage references for the botsteps
    @param list axes: Array of axis names ['x', 'y', ...] whose potentiometers should be set
    @param int value: The value to set the digital potentiometer to.
    """
    self.BuildAndSendPayload(
      host_action_command_dict['SET_POT_VALUE'], 
      EncodeAxes(axes), 
      value
    )
    

  def SetBeep(self, frequency, duration):
    """
    Play a tone of the specified frequency for the specified duration.
    @param int frequency: Frequency of the tone, in hz
    @param int duration: Duration of the tone, in ms
    """
    self.BuildAndSendPayload(
      host_action_command_dict['SET_BEEP'], 
      EncodeUint16(frequency), 
      EncodeUint16(duration), 
      0x00
    )

  def SetRGBLED(self, r, g, b, blink):
    """
    Set the brightness and blink rate for RBG LEDs
    @param int r: The r value (0-255) for the LEDs
    @param int g: The g value (0-255) for the LEDs
    @param int b: The b value (0-255) for the LEDs
    @param int blink: The blink rate (0-255) for the LEDs
    """
    self.BuildAndSendPayload(
      host_action_command_dict['SET_RGB_LED'], 
      r, 
      g, 
      b, 
      blink, 
      0x00
    )
    

  def RecallHomePositions(self, axes):
    """
    Recall and move to the home positions written to the EEPROM
    @param axes: Array of axis names ['x', 'y', ...] whose position should be saved
    """
    self.BuildAndSendPayload(
      host_action_command_dict['RECALL_HOME_POSITIONS'], 
      EncodeAxes(axes)
    )

  def Init(self):
    """
    Initialize the machine to a default state
    """
    self.BuildAndSendPayload(host_query_command_dict['INIT'])

  def ToolQuery(self, tool_index, command, tool_payload = None):
    """
    Query a toolhead for some information
    @param int tool_index: toolhead index
    @param int command: command to send to the toolhead
    @param bytearray tool_payload: payload that goes along with the command, or None
           if the command does not have a payload
    @return bytearray payload: received from the tool
    """
    if tool_index > max_tool_index or tool_index < 0:
      raise ProtocolError(1)

    if tool_payload != None:
      return self.BuildAndSendPayload(
        host_query_command_dict['TOOL_QUERY'], 
        tool_index, 
        command, 
        tool_payload
      )
    else:
      return self.BuildAndSendPayload(
        host_query_command_dict['TOOL_QUERY'], 
        tool_index, 
        command
      )

  def ReadFromEEPROM(self, offset, length):
    """
    Read some data from the machine. The data structure is implementation specific.
    @param byte offset: EEPROM location to begin reading from
    @param int length: Number of bytes to read from the EEPROM (max 31)
    @return byte array of data read from EEPROM
    """
    if length > maximum_payload_length - 1:
      raise EEPROMLengthError(length)

    response = self.BuildAndSendPayload(
      host_query_command_dict['READ_FROM_EEPROM'], 
      EncodeUint16(offset), 
      length
    )
    return response[1:]

  def WriteToEEPROM(self, offset, data):
    """
    Write some data to the machine. The data structure is implementation specific.
    @param byte offset: EEPROM location to begin writing to
    @param int data: Data to write to the EEPROM
    """
    if len(data) > maximum_payload_length - 4:
      raise EEPROMLengthError(len(data))

    response = self.BuildAndSendPayload(
      host_query_command_dict['WRITE_TO_EEPROM'], 
      EncodeUint16(offset), 
      len(data), 
      data
    )

    if response[1] != len(data):
      raise EEPROMMismatchError(response[1])

  def GetAvailableBufferSize(self):
    """
    Gets the available buffer size
    @return Available buffer size, in bytes
    """

    response = self.BuildAndSendPayload(host_query_command_dict['GET_AVAILABLE_BUFFER_SIZE'])
    [response_code, buffer_size] = UnpackResponse('<BI', response)

    return buffer_size

  def GetPosition(self):
    """
    Gets the current machine position
    @return tuple containing the 3D position the machine is currently located at, 
    and the endstop states.
    """
    response = self.BuildAndSendPayload(host_query_command_dict['GET_POSITION'])
    [response_code, x, y, z, axes_bits] = UnpackResponse('<BiiiB', response)

    return [x, y, z], axes_bits

  def AbortImmediately(self):
    """
    Stop the machine by disabling steppers, clearing the command buffers, and 
    instructing the toolheads to shut down
    """
    resposne = self.BuildAndSendPayload(host_query_command_dict['ABORT_IMMEDIATELY'])

  def PlaybackCapture(self, filename):
    """
    Instruct the machine to play back (build) a file from it's SD card.
    @param str filename: Name of the file to print. Should have been retrieved by 
    """
    response = self.BuildAndSendPayload(
      host_query_command_dict['PLAYBACK_CAPTURE'], 
      filename, 
      0x00
    )

    [response_code, sd_response_code] = UnpackResponse('<BB', response)

    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

  def GetNextFilename(self, reset):
    """
    Get the next filename from the machine
    @param boolean reset: If true, reset the file index to zero and return the first 
    available filename.
    """
    if reset == True:
      flag = 1
    else:
      flag = 0
    response = self.BuildAndSendPayload(
      host_query_command_dict['GET_NEXT_FILENAME'], 
      flag
    )
   
    [response_code, sd_response_code, filename] = UnpackResponseWithString('<BB', response)

    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

    return filename

  def GetBuildName(self):
    """
    Get the build name of the file printing on the machine, if any.
    @param str filename: The filename of the current print 
    """
    response = self.BuildAndSendPayload(host_query_command_dict['GET_BUILD_NAME'])
    [response_code, filename] = UnpackResponseWithString('<B', response)

    return filename

  def GetExtendedPosition(self):
    """
    Gets the current machine position
    @return tuple position: containing the 5D position the machine is currently located
    at, and the endstop states.
    """
    response = self.BuildAndSendPayload(host_query_command_dict['GET_EXTENDED_POSITION'])
  
    [response_code,
     x, y, z, a, b,
     endstop_states] = UnpackResponse('<BiiiiiH', response)

    # TODO: fix the endstop bit encoding, it doesn't make sense.
    return [x, y, z, a, b], endstop_states

  def QueuePoint(self, point, rate):
    """
    Move the toolhead to a new position at the given rate
    @param list position array 3D position to move to. All dimension should be in steps.
    @param double rate: Movement speed, in steps/??
    """
    if len(point) != self.PointLength:
      raise PointLengthError(len(point))
    self.BuildAndSendPayload(
      host_action_command_dict['QUEUE_POINT'], 
      [EncodeInt32(cor) for cor in point], 
      EncodeUint32(rate)
    )

  def SetPosition(self, position):
    """
    Inform the machine that it should consider this p
    @param list position: 3D position to set the machine to, in steps.
    """
    if len(position) != self.PointLength:
      raise PointLengthError(len(position))
    self.BuildAndSendPayload(
      host_action_command_dict['SET_POSITION'], 
      [EncodeInt32(cor) for cor in position]
    )

  def FindAxesMinimums(self, axes, rate, timeout):
    """
    Move the toolhead in the negativedirection, along the specified axes,
    until an endstop is reached or a timeout occurs.
    @param list axes: Array of axis names ['x', 'y', ...] to move
    @param double rate: Movement rate, in steps/??
    @param double timeout: Amount of time to move (TODO: units?) before halting the command
    """
    self.BuildAndSendPayload(
      host_action_command_dict['FIND_AXES_MINIMUMS'], 
      EncodeAxes(axes), 
      EncodeUint32(rate), 
      EncodeUint16(timeout)
    )
  
  def FindAxesMaximums(self, axes, rate, timeout):
    """
    Move the toolhead in the positive direction, along the specified axes,
    until an endstop is reached or a timeout occurs.
    @param list axes: Array of axis names ['x', 'y', ...] to move
    @param double rate: Movement rate, in steps/??
    @param double timeout: Amount of time to move (TODO: units?) before halting the command
    """
    self.BuildAndSendPayload(
      host_action_command_dict['FIND_AXES_MAXIMUMS'], 
      EncodeAxes(axes), 
      EncodeUint32(rate), 
      EncodeUint16(timeout)
    )

  def ToolActionCommand(self, tool_index, command, tool_payload = None):
    """
    Send a command to a toolhead
    @param int tool_index: toolhead index
    @param int command: command to send to the toolhead
    @param bytearray tool_payload: payload that goes along with the command
    """
    if tool_index > max_tool_index or tool_index < 0:
      raise ToolIndexError(tool_index)

    if tool_payload != None:
      self.BuildAndSendPayload(
        host_action_command_dict['TOOL_ACTION_COMMAND'], 
        tool_index, 
        command, 
        len(tool_payload), 
        tool_payload
      )
    else:
      self.BuildAndSendPayload(
        host_action_command_dict['TOOL_ACTION_COMMAND'],
        tool_index,
        command
      )


  def QueueExtendedPoint(self, point, rate):
    """
    Move the toolhead to a new position at the given rate
    @param list position: 5D position to move to. All dimension should be in steps.
    @param double rate: Movement speed, in steps/??
    """
    if len(point) != self.ExtendedPointLength:
      raise PointLengthError(len(point))
    self.BuildAndSendPayload(
      host_action_command_dict['QUEUE_EXTENDED_POINT'], 
      [EncodeInt32(cor) for cor in point], 
      EncodeUint32(rate)
    )

  def SetExtendedPosition(self, position):
    """
    Inform the machine that it should consider this point its current point
    @param list position: 5D position to set the machine to, in steps.
    """
    if len(position) != self.ExtendedPointLength:
      raise PointLengthError(len(position))
    self.BuildAndSendPayload(
      host_action_command_dict['SET_EXTENDED_POSITION'], 
      [EncodeInt32(cor) for cor in position]
    )

  def WaitForButton(self, button, timeout, ready_on_timeout, reset_on_timeout, clear_screen):
    """
    Wait until a user either presses a button on the interface board, or a timeout occurs
    @param str button: A button, must be one of the following: up, down, left, right center.
    @param double timeout: Duration, in seconds, the bot will wait for a response.  
      A timeout of 0 indicated no timeout.  TimeoutReadyState, timeoutReset determine what 
      action is taken after timeout
    @param boolean ready_on_timeout: Bot changes to the ready state after tiemout
    @param boolean reset_on_timeout: Resets the bot on timeout
    @param boolean clear_screen: Clears the screen on buttonPress
    """
    if button == 'center':
      button = 0x01
    elif button == 'right':
      button = 0x02
    elif button == 'left':
      button = 0x04
    elif button == 'down':
      button = 0x08
    elif button == 'up':
      button = 0x10
    else:
      raise ButtonError(button)

    optionsField = 0
    if ready_on_timeout:
      optionsField |= 0x01
    if reset_on_timeout:
      optionsField |= 0x02
    if clear_screen:
      optionsField |= 0x04
    self.BuildAndSendPayload(
      host_action_command_dict['WAIT_FOR_BUTTON'], 
      button, 
      EncodeUint16(timeout), 
      optionsField
    )

  def ResetToFactory(self):
    """
    Calls factory reset on the EEPROM.  Resets all values to their factory settings.  Also soft resets the board
    """
    self.BuildAndSendPayload(
      host_action_command_dict['RESET_TO_FACTORY'],
      0x00
    )

  def QueueSong(self, song_id):
    """
    Play predefined sogns on the piezo buzzer
    @param int songId: The id of the song to play.
    """
    self.BuildAndSendPayload(
      host_action_command_dict['QUEUE_SONG'], 
      song_id
    )

  def SetBuildPercent(self, percent):
    """
    Sets the percentage done for the current build.  This value is displayed on the interface board's screen.
    @param int percent: Percent of the build done (0-100)
    """
    self.BuildAndSendPayload(
      host_action_command_dict['SET_BUILD_PERCENT'], 
      percent, 
      0x00
    )

  def DisplayMessage(self, row, col, message, timeout, clearExisting, lastInGroup, waitForButton):
    """
    Display a message to the screen
    @param int row: Row to draw the message at
    @param int col: Column to draw the message at
    @param str message: Message to write to the screen
    @param int timeout: Amount of time to display the message for, in seconds. 
                   If 0, leave the message up indefinately.
    @param boolean clearExisting: flag.  If True, This will clear the existing message buffer and timeout
    @param boolean lastInGroup: flag.  If true, signifies that this message is the last in a group of messages
    @param boolean waitForButton: flag.  If true, waits for a button to be pressed before clearing the screen
    """
    bitField = 0
    if clearExisting:
      bitField |= 0x01
    if lastInGroup:
      bitField |= 0x02
    if waitForButton:
      bitField |= 0x04
    self.BuildAndSendPayload(
      host_action_command_dict['DISPLAY_MESSAGE'], 
      bitField, 
      col, 
      row, 
      timeout, 
      message, 
      0x00
    )

  def BuildStartNotification(self, command_count, build_name):
    """
    Notify the machine that a build has been started
    @param int command_count Number of host commands in the build
    @param str build_name Name of the build
    """
    self.BuildAndSendPayload(
      host_action_command_dict['BUILD_START_NOTIFICATION'], 
      EncodeUint32(command_count), 
      build_name, 
      0x00
    )

  def BuildEndNotification(self):
    """
    Notify the machine that a build has been stopped.
    """
    self.BuildAndSendPayload(host_action_command_dict['BUILD_END_NOTIFICATION'])


  def GetToolheadVersion(self, tool_index):
    """
    Get the firmware version number of the specified toolhead
    @return double Version number
    """
    payload = bytearray()
    AddObjToPayload(payload, EncodeUint16(s3g_version))
   
    response = self.ToolQuery(tool_index,slave_query_command_dict['GET_VERSION'], payload)
    [response_code, version] = UnpackResponse('<BH', response)

    return version

  def GetPIDState(self, tool_index):
    """
    Retrieve the state variables of the PID controller.  This is intended for tuning the PID Constants
    @param int tool_index: Which tool index to query for information
    @return dictionary The terms associated with the tool_index'sError Term, Delta Term, Last Output 
      and the platform's Error Term, Delta Term and Last Output
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PID_STATE'])
    [response_code, exError, exDelta, exLast, plError, plDelta, plLast] = UnpackResponse('<Bhhhhhh', response)
    PIDVals = {
      "ExtruderError"          : exError,
      "ExtruderDelta"          : exDelta,
      "ExtruderLastTerm"       : exLast,
      "PlatformError"          : plError,
      "PlatformDelta"          : plDelta,
      "PlatformLastTerm"       : plLast,
    }
    return PIDVals

  def GetToolStatus(self, tool_index):
    """
    Retrieve some information about the tool
    @param int tool_index: The tool we would like to query for information
    @return A dictionary containing status information about the tool_index
      ExtruderReady : The extruder has reached target temp
      PlatformError: an error was detected with the platform heater (if the tool supports one).  
        The platform heater will fail if an error is detected with the sensor (thermocouple) 
        or if the temperature reading appears to be unreasonable.
      ExtruderError: An error was detected with the extruder heater (if the tool supports one).  
        The extruder heater will fail if an error is detected with the sensor (thermocouple) or 
        if the temperature reading appears to be unreasonable
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOL_STATUS'])
    [resonse_code, bitfield] = UnpackResponse('<BB', response)

    bitfield = DecodeBitfield8(bitfield)

    returnDict = {
      "ExtruderReady" : bool(bitfield[0]),
      "PlatformError" : bool(bitfield[6]),
      "ExtruderError" : bool(bitfield[7]),
    }
    return returnDict
  
  def SetServo1Position(self, tool_index, theta):
    """
    Sets the tool_index's servo as position 1 to a certain angle 
    @param int tool_index: The tool that will be set
    @param int theta: angle to set the servo to
    """
    payload = bytearray()
    AddObjToPayload(payload, theta)
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_SERVO_1_POSITION'], payload)

  def ToolheadAbort(self, tool_index):
    """
    Used to terminate a build during printing.  Disables any engaged heaters and motors
    @param int tool_index: the tool which is to be aborted
    """
    self.ToolActionCommand(tool_index, slave_action_command_dict['ABORT'], bytearray())

  def ToolheadPause(self, tool_index):
    """
    This function is intended to be called infrequently by the end user to pause the toolhead 
    and make various adjustments during a print
    @param int tool_index: The tool which is to be paused
    """
    self.ToolActionCommand(tool_index, slave_action_command_dict['PAUSE'], bytearray())

  def ToggleMotor1(self, tool_index, toggle, direction):
    """
    Toggles the motor of a certain toolhead to be either on or off.  Can also set direction.
    @param int tool_index: the tool's motor that will be set
    @param boolean toggle: The enable/disable flag.  If true, will turn the motor on.  If false, disables the motor.
    @param boolean direction: If true, sets the motor to turn clockwise.  If false, sets the motor to turn counter-clockwise
    """
    payload = bytearray()
    bitfield = 0
    if toggle:
      bitfield |= 0x01
    if direction:
      bitfield |= 0x02
    AddObjToPayload(payload, bitfield)
    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_MOTOR_1'], payload)

  def SetMotor1SpeedRPM(self, tool_index, duration):
    """
    This sets the motor speed as an RPM value
    @param int tool_index : The tool's motor that will be set
    @param int duration : Durtation of each rotation, in microseconds
    """
    payload = bytearray()
    AddObjToPayload(payload, EncodeUint32(duration))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_MOTOR_1_SPEED_RPM'], payload)

  def GetMotor1Speed(self, tool_index):
    """
    Gets the toohead's motor speed in Rotations per Minute (RPM)
    @param int tool_index: The tool index that will be queried for Motor speed
    @return int Duration of each rotation, in miliseconds
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_MOTOR_1_SPEED_RPM'])
    [response_code, speed] = UnpackResponse('<BI', response)
    return speed

  def GetToolheadTemperature(self, tool_index):
    """
    Retrieve the toolhead temperature
    @param int tool_index: Toolhead Index
    @return int temperature: reported by the toolhead
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOLHEAD_TEMP'])
    [response_code, temperature] = UnpackResponse('<BH', response)

    return temperature

  def IsToolReady(self, tool_index):
    """
    Determine if the tool is at temperature, and is therefore ready to be used.
    @param int tool_index: Toolhead Index
    @return boolean isReady: True if tool is done heating, false otherwise
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['IS_TOOL_READY'])
    [response_code, ready] = UnpackResponse('<BB', response)
    isReady = False
    if ready == 1:
      isReady = True
    elif ready == 0:
      isReady = False
    else:
      raise HeatElementReadyError(ready)
    return isReady

  def ReadFromToolheadEEPROM(self, tool_index, offset, length):
    """
    Read some data from the toolhead. The data structure is implementation specific.
    @param byte offset: EEPROM location to begin reading from
    @param int length: Number of bytes to read from the EEPROM (max 31)
    @return byte array: of data read from EEPROM
    """
    if length > maximum_payload_length - 1:
      raise EEPROMLengthError(length)

    payload = bytearray()
    AddObjToPayload(payload,
                         [EncodeUint16(offset),
                          length])

    response = self.ToolQuery(tool_index, slave_query_command_dict['READ_FROM_EEPROM'], payload)

    return response[1:]

  def WriteToToolheadEEPROM(self, tool_index, offset, data):
    """
    Write some data to the toolhead. The data structure is implementation specific.
    @param int tool_index: Index of tool to access
    @param byte offset: EEPROM location to begin writing to
    @param list data: Data to write to the EEPROM
    """
    # TODO: this length is bad
    if len(data) > maximum_payload_length - 6:
      raise EEPROMLengthError(len(data))

    payload = bytearray()
    AddObjToPayload(
      payload, 
      [EncodeUint16(offset),
      len(data),
      data]
    )

    response = self.ToolQuery(tool_index, slave_query_command_dict['WRITE_TO_EEPROM'], payload)

    if response[1] != len(data):
      raise EEPROMMismatchError(response[1])

  def GetPlatformTemperature(self, tool_index):
    """
    Retrieve the build platform temperature
    @param int tool_index: Toolhead Index
    @return int temperature: reported by the toolhead
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PLATFORM_TEMP'])
    [response_code, temperature] = UnpackResponse('<BH', response)

    return temperature

  def GetToolheadTargetTemperature(self, tool_index):
    """
    Retrieve the toolhead target temperature (setpoint)
    @param int tool_index: Toolhead Index
    @return int temperature: that the toolhead is attempting to achieve
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOLHEAD_TARGET_TEMP'])
    [response_code, temperature] = UnpackResponse('<BH', response)

    return temperature

  def GetPlatformTargetTemperature(self, tool_index):
    """
    Retrieve the build platform target temperature (setpoint)
    @param int tool_index: Toolhead Index
    @return int temperature: that the build platform is attempting to achieve
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PLATFORM_TARGET_TEMP'])
    [response_code, temperature] = UnpackResponse('<BH', response)

    return temperature

  def IsPlatformReady(self, tool_index):
    """
    Determine if the platform is at temperature, and is therefore ready to be used.
    @param int tool_index: Toolhead Index
    @return boolean isReady: true if the platform is at target temperature, false otherwise
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['IS_PLATFORM_READY'])
    [response_code, ready] = UnpackResponse('<BB', response)

    isReady = False
    if ready == 1:
      isReady = True
    elif ready == 0:
      isReady = False
    else:
      raise HeatElementReadyError(ready)
    return isReady

  def ToggleFan(self, tool_index, state):
    """
    Turn the fan output on or off
    @param int tool_index: Toolhead Index
    @param boolean state: If True, turn the fan on, otherwise off.
    """

    payload = bytearray()
    if state == True:
      AddObjToPayload(payload, 0x01)
    else:
      AddObjToPayload(payload, 0x00)
    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_FAN'], payload)

  def ToggleValve(self, tool_index, state):
    """
    Turn the valve output on or off
    @param int tool_index: Toolhead Index
    @param boolean state: If True, turn the valvue on, otherwise off.
    """

    payload = bytearray()
    if state == True:
      AddObjToPayload(payload, 0x01)
    else:
      AddObjToPayload(payload, 0x00)

    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_VALVE'], payload)

  def ToolheadInit(self, tool_index):
    """
    Resets a certain tool_index to its initialized boot state, which consists of:
      resetting target temp to 0
      turn off all outputs
      detaching all servo devices
      sesetting motor speed to 0
    @param int tool_index: The tool to re-initialize
    """
    self.ToolActionCommand(tool_index, slave_action_command_dict['INIT'])

  def SetToolheadTemperature(self, tool_index, temperature):
    """
    Set a certain toolhead's temperature
    @param int tool_index: Toolhead Index
    @param int Temperature: Temperature to heat up to in Celcius
    """
    payload = bytearray()
    AddObjToPayload(payload, EncodeUint16(temperature))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_TOOLHEAD_TARGET_TEMP'], payload)


  def SetPlatformTemperature(self, tool_index, temperature):
    """
    Set the platform's temperature
    @param int tool_index: Platform Index
    @param int Temperature: Temperature to heat up to in Celcius
    """
    payload = bytearray()
    AddObjToPayload(payload, EncodeUint16(temperature))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_PLATFORM_TEMP'], payload)
