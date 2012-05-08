#Error Report

## Makerbot Test Explanations

### CommonFunctionTests
This suite tests any shared functions contained within Makerbottests.py

### s3gPacketTests
This suite tests the packets that are sent to the machine, and ensures the proper errors (if any) are thrown if a malformed packet is sent to a bot

### s3gSendReceiveTests
This suite tests all functions of the s3g python module, and ensures that all packets can be sent to the machine, and that the machine sends the proper response back.  These tests are pretty simple, and only involve executing the command, and asserting true if no errors are thrown (any errors that arrise will prohibit the assertion from being executed)

### s3gFunctionTests
These tests ensure that the machine processes the command correctly and takes the correct action

### s3gSDCardTests
This suite tests the machine operations that revolve around the SD card.  They are separate from the s3gFunctionTests because they require an SD card to be inserted into the bot.  The SD card in the bot should have the same contents of testFiles

##Errors found
All errors listed below were discovered when connecting to a Replicator using version 5.2 of the MB firmware.

### Init
Currently Init does not reset all axes positions to 0 

###ToolheadInit
Does not reset the toolhead temperature to 0

### Get Next Filename
This function should be able to send the volume name of the sd card.  It does not work as intended, however, since volume names such as 'NO NAME' return simply as NO

###GetMotherboardStatus
This function has yet to be implemented into the firmware (at least for the most recent pull (5/3 at 18:49) of the master branch)

###GetCommunicationStats
This function is spec'd to use number 26, but the latest pull of the firmware (5/3 at 18:49) has it defined to 25
Communicaiton stats dont seem to be incrementing correctly.  This could be because I am not in debug mode.  

###BuildEndNotification
This function should end a build.  But, after the build End Notification signal is sent, the bot still thinks it is building the file it was building before

###Delay
Should delay in microseconds, delays in miliseconds instead

###QueueExtendedPointNew
Points are not being queued up correctly.  For instance, starting at [10, 10, 10, 10, 10] and moving to [1, 2, 3, 4, 5], the replicator ends up at [46, 6, 3, 4, 5]

###GetToolStatus
GetToolStatus returns a bitfield containing information about the extruder.  The 0'th bit should be whether or not the extruder is ready.  But, when the extruder is heating up, it does not agree with s3g's IsToolReady function.  All other values are correct, though.

###WaitForButton
Throwing the timeout Reset flag, and letting the timeout elapse causes the mightyboard to be in a constant loop of resetting.
Throwing the Timeout ready state flag and letting the timeout elapse causes the center button to constantly flash

###SetPotentiometerValue
I measured the vRef of both the A and B axes WITHOUT the botstep plugged in.  Using SetPotentiometerValue, I set the A and B axes pot values to 127 and took a reading of 1.958V.  I then set the pot values to 0, and took a reading of 1.958.

###SetRGBLED
Setting different colours works fine, but setting a blink value of either 0, 128 or 256, nothing happened

###SetBeep
Giving a frequency of 261.626 for 3 seconds resulted in no audible sound
