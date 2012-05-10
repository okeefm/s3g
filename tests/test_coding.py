import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import s3g
import struct

class EncoderTests(unittest.TestCase):
  def test_decode_bitfield8(self):
    field1 = 0
    vals1 = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
    for val in vals1:
      field1 |= val
    self.assertTrue(s3g.DecodeBitfield8(field1), [1, 1, 1, 1, 1, 1, 1, 1])
    field2 = 0
    vals2 = [0x01, 0x04, 0x10, 0x40]
    for val in vals2:
      field2 |= val
    self.assertTrue(s3g.DecodeBitfield8(field2), [1, 0, 1, 0, 1, 0, 1, 0])
    field3 = 0
    vals3 = [0x01, 0x02]
    for val in vals3:
      field3 |= val
    self.assertTrue(s3g.DecodeBitfield8(field3), [1, 1, 0, 0, 0, 0, 0, 0, 0])
    self.assertTrue(s3g.DecodeBitfield8(0), [0, 0, 0, 0, 0, 0, 0, 0])

  def test_decode_bitfield8_pathogenic(self):
    field = 0
    field |= 0x80 + 0x80
    self.assertRaises(TypeError, s3g.DecodeBitfield8, field)


  def test_encode_int32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [-2147483648,  '\x00\x00\x00\x80'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
    ]
    for case in cases:
      assert s3g.EncodeInt32(case[0]) == case[1]
    
  def test_encode_uint32(self):
    cases = [
      [0,            '\x00\x00\x00\x00'],
      [2147483647,   '\xFF\xFF\xFF\x7F'],
      [4294967295,   '\xFF\xFF\xFF\xFF'],
    ]
    for case in cases:
      assert s3g.EncodeUint32(case[0]) == case[1]

  def test_encode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      assert s3g.EncodeUint16(case[0]) == case[1]

  def test_decode_int32(self):
    cases = [
      [0,       '\x00\x00\x00\x00'],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], s3g.DecodeInt32(case[1]))

  def test_decode_int32_bytearray(self):
    cases = [
      [0, bytearray('\x00\x00\x00\x00')],
      [-65536,  '\x00\x00\xFF\xFF'],
      [16,      '\x10\x00\x00\x00'],
    ]
    for case in cases:
      self.assertEqual(case[0], s3g.DecodeInt32(case[1]))

  def test_decode_uint16(self):
    cases = [
      [0,       '\x00\x00'],
      [32767,   '\xFF\x7F'],
      [65535,   '\xFF\xFF'],
    ]
    for case in cases:
      self.assertEqual(s3g.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_bytearray(self):
    byteArrayCases = [
      [0,       bytearray('\x00\x00')],
      [32767,   bytearray('\xff\x7f')],
      [65535,   bytearray('\xff\xff')],
    ]
    for case in byteArrayCases:
      self.assertEqual(s3g.DecodeUint16(case[1]), case[0])

  def test_decode_uint16_pathological_fail(self):
    failCase = [0, bytearray('\x00\x00\x00')]
    self.assertRaises(struct.error, s3g.DecodeUint16, failCase[1])

  def test_encode_axes(self):
    cases = [
      [['x','y','z','a','b'], 0x1F],
      [['x'],                 0x01],
      [['y'],                 0x02],
      [['z'],                 0x04],
      [['a'],                 0x08],
      [['b'],                 0x10],
      [[],                    0x00],
    ]
    for case in cases:
      assert s3g.EncodeAxes(case[0]) == case[1]

  def test_unpack_response_no_format(self):
    self.assertRaises(s3g.ProtocolError,s3g.UnpackResponse,'','abcde')

  def test_unpack_response_short_data(self):
    self.assertRaises(s3g.ProtocolError,s3g.UnpackResponse,'<I','abc')

  def test_unpack_response(self):
    expected_data = [1,'a','b','c']
    data = s3g.UnpackResponse('<Iccc','\x01\x00\x00\x00abc')
    for i in range(0, len(expected_data)):
      assert(data[i] == expected_data[i])

  def test_unpack_response_with_string_no_format(self):
    expected_string = 'abcde\x00'
    data = s3g.UnpackResponseWithString('',expected_string)
    assert(len(data) == 1)
    assert data[0] == expected_string

  def test_unpack_response_with_string_missing_string(self):
    self.assertRaises(s3g.ProtocolError,s3g.UnpackResponseWithString,'<I','abcd')

  def test_unpack_response_with_string(self):
    expected_data = [1,'a','b','c','ABCDE\x00']
    data = s3g.UnpackResponseWithString('<Iccc','\x01\x00\x00\x00abcABCDE\x00')
    for i in range(0, len(expected_data)):
      assert(data[i] == expected_data[i])

if __name__ == "__main__":
  unittest.main()
