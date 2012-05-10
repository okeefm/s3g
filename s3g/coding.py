import struct
import array

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
