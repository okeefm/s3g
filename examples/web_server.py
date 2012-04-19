"""
Start a web server that can proxy requests to the machine

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
* web.py: http://webpy.org
"""
# To use this example without installing s3g, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import serial
import optparse
import web
import io
import json

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
(options, args) = parser.parse_args()



if __name__ == '__main__':
  r = s3g.s3g()

  # TODO: just use a real serial port.
#  outputstream = io.BytesIO() # Stream that we will send responses on
#  inputstream = io.BytesIO()  # Stream that we will receive commands on
#  r.file = io.BufferedRWPair(outputstream, inputstream)
  r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

  urls = (
    '/(.*)', 'index'
  )

  temperature_data = []

  class index:
    def GET(self, name):
      # TODO: Haha, this is dnagerous???
      bound_mth = getattr(r, name)

      # TODO: Fake temperature!
#      temperature = 1234
#      response_payload = bytearray()
#      response_payload.append(s3g.response_code_dict['SUCCESS'])
#      response_payload.extend(s3g.EncodeUint16(temperature))
#      outputstream.write(s3g.EncodePayload(response_payload))
#      outputstream.seek(0)
      temperature_data.append([len(temperature_data), bound_mth(0)])
      response = {"label" : "Toolhead 0 Temperature", "data" : temperature_data}

      web.header('Content-Type', 'application/json')

      print '>>' + json.dumps(response) + '<<'

      return json.dumps(response)

  app = web.application(urls, globals())
  app.run()
