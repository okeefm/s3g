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
import json
import BaseHTTPServer
import SimpleHTTPServer
import SocketServer
import threading

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-a", "--httpaddress", dest="httpaddress",
                  help="http address", default="127.0.0.1")
parser.add_option("-o", "--httpport", dest="httpport",
                  help="http port", default=8080)
(options, args) = parser.parse_args()


if __name__ == '__main__':
    r = s3g.s3g()
 
    r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)
 
    tool_0_temp_data = []
    tool_1_temp_data = []
    platform_temp_data = []

    def update_temp_thread():
        t = threading.Timer(2.0, update_temp_thread)
        t.start()

        tool_0_temp_data.append([len(tool_0_temp_data), r.GetToolheadTemperature(0)])
        tool_1_temp_data.append([len(tool_1_temp_data), r.GetToolheadTemperature(1)])
        platform_temp_data.append([len(platform_temp_data), r.GetPlatformTemperature(0)])

#        if (tool_0_temp_data != None):
#            if (len(tool_0_temp_data) > 200):
#                tool_0_temp_data = tool_0_temp_data[-200:]
#                tool_1_temp_data = tool_1_temp_data[-200:]


    update_temp_thread()
    
 
    class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(s):
            """Respond to a GET request."""
            # If the request was for a temperature, handle it.
            print s.path
            if s.path == '/temp':
#                tool_0_temp_data.append([len(tool_0_temp_data), r.GetToolheadTemperature(0)])
#                tool_1_temp_data.append([len(tool_1_temp_data), r.GetToolheadTemperature(1)])
 
                #if (tool_0_temp_data != None):
                #    if (len(tool_0_temp_data) > 200):
                #        tool_0_temp_data = tool_0_temp_data[-200:]
                #        tool_1_temp_data = tool_1_temp_data[-200:]
             
                response = {"tool_0_temp" : {"label" : "Toolhead 0 Temperature", "data" : tool_0_temp_data},
                            "tool_1_temp" : {"label" : "Toolhead 1 Temperature", "data" : tool_1_temp_data},
                            "platform_temp" : {"label" : "Platform Temperature", "data" : platform_temp_data}}
                content = json.dumps(response)
             
                s.send_response(200)
                s.send_header("Content-Type",   "application/json")
                s.end_headers()
                s.wfile.write(content)
                return
             
            # Otherwise pass it down
            s.path = '/web_server/' + s.path 
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(s)
            
    httpd = SocketServer.TCPServer((options.httpaddress, options.httpport), MyHandler)
 
    print "serving at port", options.httpport
    httpd.serve_forever()
