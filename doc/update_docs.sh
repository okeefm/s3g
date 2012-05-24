#!/bin/sh

# Build the documents. Requires that GraphViz be installed.

dot PacketStreamDecoder.dot -Tpng > PacketStreamDecoder.png
dot SendCommand.dot -Tpng > SendCommand.png
dot CheckResponseCode.dot -Tpng > CheckResponseCode.png
dot GCodeStateMachine.dot -Tpng > GCodeStateMachine.png
dot MCodeStateMachine.dot -Tpng > MCodeStateMachine.png

mscgen -i HostCommandSuccess.msc -T png
mscgen -i ToolCommandSuccess.msc -T png
mscgen -i HostToolCommandSuccess.msc -T png

