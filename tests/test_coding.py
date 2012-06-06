import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import struct
from s3g import Encoder, errors

class EncoderTests(unittest.TestCase):

  def test_decode_bitfield8(self):
    field1 = 0
    vals1 = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    for val in vals1:
      field1 |= val
    self.assertTrue(Encoder.DecodeBitfield8(field1), [1, 1, 1, 1, 1, 1, 1, 1])
    field2 = 0
    vals2 = [0x01, 0x04, 0x10, 0x40]
    for val in vals2:
      field2 |= val
    self.assertTrue(Encoder.DecodeBitfield8(field2), [1, 0, 1, 0, 1, 0, 1, 0])
    field3 = 0
    vals3 = [0x01, 0x02]
    for val in vals3:
      field3 |= val
    self.assertTrue(Encoder.DecodeBitfield8(field3), [1, 1, 0, 0, 0, 0, 0, 0, 0])
    self.assertTrue(Encoder.DecodeBitfield8(0), [0, 0, 0, 0, 0, 0, 0, 0])

  def test_decode_bitfield8_pathogenic(self):
    field = 0
    field |= 0x80 + 0x80
    self.assertRaises(TypeError, Encoder.DecodeBitfield8, field)


  def test_encode_int32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [-2147483648,  '\x00\x00\x00\x80'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
    ]
    for case in cases:
      assert Encoder.EncodeInt32(case[0]) == case[1]
    
  def test_encode_uint32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
      [4294967295,   '\xFF\xFF\xFF\xFF'],
    ]
    for case in cases:
      assert Encoder.EncodeUint32(case[0]) == case[1]

  def test_encode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      assert Encoder.EncodeUint16(case[0]) == case[1]

  def test_decode_int32(self):
    cases = [
      [0,       '\x00\x00\x00\x00'],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], Encoder.DecodeInt32(case[1]))

  def test_decode_int32_bytearray(self):
    cases = [
      [0, bytearray('\x00\x00\x00\x00')],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], Encoder.DecodeInt32(case[1]))

  def test_decode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      self.assertEqual(Encoder.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_bytearray(self):
    byteArrayCases = [
      [0,       bytearray('\x00\x00')],
      [32767,   bytearray('\xff\x7f')],
      [65535,   bytearray('\xff\xff')],
    ]
    for case in byteArrayCases:
      self.assertEqual(Encoder.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_pathological_fail(self):
    failCase = [0, bytearray('\x00\x00\x00')]
    self.assertRaises(struct.error, Encoder.DecodeUint16, failCase[1])

  def test_encode_axes(self):
    cases = [
      [['X', 'Y', 'Z', 'A', 'B'], 0x1F],
      [['x','y','z','a','b'], 0x1F],
      [['x'],                 0x01],
      [['y'],                 0x02],
      [['z'],                 0x04],
      [['a'],                 0x08],
      [['b'],                 0x10],
      [[],                    0x00],
    ]
    for case in cases:
      assert Encoder.EncodeAxes(case[0]) == case[1]

  def test_unpack_response_no_format(self):
    b = bytearray()
    b.extend('abcde')
    self.assertRaises(errors.ProtocolError,Encoder.UnpackResponse,'',b)

  def test_unpack_response_short_data(self):
    b = bytearray()
    b.extend('abc')
    self.assertRaises(errors.ProtocolError,Encoder.UnpackResponse,'<I',b)

  def test_unpack_response(self):
    expected_data = [1,'a','b','c']
    b = bytearray()
    b.extend(Encoder.EncodeUint32(1))
    for data in expected_data[1:]:
      b.append(data)
    data = Encoder.UnpackResponse('<Iccc',b)
    for i in range(0, len(expected_data)):
      assert(data[i] == expected_data[i])

  def test_unpack_response_with_string_empty_string(self):
    expected_string = '\x00'
    b = bytearray()
    b.append(expected_string)
    data = Encoder.UnpackResponseWithString('', b)
    self.assertEqual(expected_string, data[0])

  def test_unpack_response_with_string_no_format(self):
    expected_string = 'abcde\x00'
    b = bytearray()
    b.extend(expected_string)
    data = Encoder.UnpackResponseWithString('',b)
    assert(len(data) == 1)
    assert data[0] == expected_string

  def test_unpack_response_with_string_missing_string(self):
    b = bytearray()
    b.extend('abcd')
    self.assertRaises(errors.ProtocolError,Encoder.UnpackResponseWithString,'<I',b)

  def test_unpack_response_with_string(self):
    expected_data = [1, 'a', 'b', 'c', 'ABCDE\x00']
    b = bytearray()
    b.extend(Encoder.EncodeUint32(1))
    for data in expected_data[1:-1]:
      b.append(data)
    b.extend(expected_data[-1])
    data = Encoder.UnpackResponseWithString('<Iccc',b)
    for expected, d in zip(expected_data, data):
      self.assertEqual(expected, d)

  def test_unpack_response_with_non_null_terminated_string(self):
    expected_data = 'ABCDE'
    b = bytearray()
    b.extend(expected_data)
    self.assertRaises(errors.ProtocolError, Encoder.UnpackResponseWithString, '', b)

if __name__ == "__main__":
  unittest.main()
