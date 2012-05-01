#!/bin/sh

# Build the documents. Requires that GraphViz be installed.

dot PacketStreamDecoder.dot -Tpng > PacketStreamDecoder.png
dot SendCommand.dot -Tpng > SendCommand.png
dot CheckResponseCode.dot -Tpng > CheckResponseCode.png

