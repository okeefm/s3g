import struct
import array

from errors import *

def AddObjToPayload(payload, obj):
  """Adds an object to the payload

  Objects come in three flavors: single objects, iterators and iterators nested in iterators.
  Because we cannot extend iterators of iterators, we use this recursive function to break all
  iterators down into single objects and add them that way.

  @param bytearray payload: A payload in the form of a bytearray we add the obj to
  @param obj: The obj we want to add to the payload
  """
  try:
    payload.append(obj)
  except:
    for o in obj:
      AddObjToPayload(payload, o)

def EncodeInt32(number):
  """
  Encode a 32-bit signed integer as a 4-byte string
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<i', number)

def EncodeUint32(number):
  """
  Encode a 32-bit unsigned integer as a 4-byte string
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<I', number)

def DecodeInt32(data):
  """
  Decode a 4-byte string into a 32-bit signed integer
  @param data: byte array of size 4 that represents the integer
  @param return: decoded integer
  """
  if isinstance(data, bytearray):
    data = array.array('B', data)
  return struct.unpack('<i', data)[0]

def EncodeUint16(number):
  """
  Encode a 16-bit unsigned integer as a 2-byte string
  @param number 
  @return byte array of size 2 that represents the integer
  """
  return struct.pack('<H', number)

def DecodeUint16(data):
  """
  Decode a 2-byte string as a 16-bit integer
  @param data byte array of size 2 that represents the integer
  @return decoded integer
  """
  #Byte arrays need to be converted into arrays to be unpackable by struct
  if isinstance(data, bytearray):
    data = array.array('B', data)
  return struct.unpack('<H', data)[0]
    
def DecodeBitfield8(bitfield):
  """
  Given a bitfield that is no greater than 8 bits, decodes it into a list of bits
  @param bitfield: The bitfield to decode
  @return list representation of the bitfield
  """
  bitString = bin(bitfield)[2:]
  if len(bitString) > 8:
    raise TypeError("Expecting bitfield of size no greater than 8, got bitfield of size %i"%(len(bitString)))
  bitList = list(bitString)
  bitList.reverse()
  for i in range(8-len(bitList)):
    bitList.append(0)
  return bitList

def EncodeAxes(axes):
  """
  Encode an array of axes names into an axis bitfield
  @param axes Array of axis names ['x', 'y', ...] 
  @return bitfield containing a representation of the axes map
  """
  # TODO: Test cases?

  axes_map = {
    'x':0x01,
    'y':0x02,
    'z':0x04,
    'a':0x08,
    'b':0x10,
  }

  bitfield = 0

  for axis in axes:
    bitfield |= axes_map[axis]

  return bitfield


def UnpackResponse(format, data):
  """
  Attempt to unpack the given data using the specified format. Throws a protocol
  error if the unpacking fails.
  
  @param format Format string to use for unpacking
  @param data Data to unpack.  We _cannot_ unpack strings!
  @return list of values unpacked, if successful.
  """

  try:
    return struct.unpack(format, buffer(data))
  except struct.error as e:
    raise ProtocolError("Unexpected data returned from machine. Expected length=%i, got=%i, error=%s"%
      (struct.calcsize(format),len(data),str(e)))

def UnpackResponseWithString(format, data):
  """
  Attempt to unpack the given data using the specified format, and with a trailing,
  null-terminated string. Throws a protocol error if the unpacking fails.
  
  @param format Format string to use for unpacking
  @param data Data to unpack, including a string if specified
  @return list of values unpacked, if successful.
  """
  #The +1 is for the null terminator of the string
  if (len(data) < struct.calcsize(format) + 1):
    raise ProtocolError("Not enough data received from machine, expected=%i, got=%i"%
      (struct.calcsize(format)+1,len(data))
    )

  #Check for a null terminator on the string
  elif (data[-1]) != 0:
    raise ProtocolError("Expected null terminated string.")

  output = UnpackResponse(format, data[0:struct.calcsize(format)])
  output += data[struct.calcsize(format):],
  return output
