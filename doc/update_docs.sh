#!/bin/sh

# Build the documents. Requires that GraphViz be installed.

dot PacketStreamDecoder.dot -Tpng > PacketStreamDecoder.png
dot SendCommand.dot -Tpng > SendCommand.png
dot CheckResponseCode.dot -Tpng > CheckResponseCode.png

mscgen -i HostCommandSuccess.msc -T png
mscgen -i ToolCommandSuccess.msc -T png
mscgen -i HostToolCommandSuccess.msc -T png

