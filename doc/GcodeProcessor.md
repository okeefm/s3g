#Processor
There are many flavors of gcode created by many programs.  To keep makerbot_driver manageable, we can only handle a subset of those commands well.  In order to allow greater compatiblity, makerbot_driver has a set of processors to convert many common gcode flavors into a gcode twhich makerbot_driver can easily use. 

##Adding Processors
We encourage users to add processors of their own into s3g.  We will accept any processor with 'example_' as a name, with without tests.  We will only accept as processor as'ProcessorX' if it has excellent unit test coverage, comparbile to other Processors.


##List of Processors
We have provided an array of common Processors for older MakerBot variants of gcode, as well as some common slicing engines.

###Processor
An interface that all processors inherit from.

###Skeinforge 50 Processor
A processor that is meant to be run on a .gcode file skeined by skeinforge-50 WITHOUT start and end gcodes.

    * Removes M104 commands if they do not include a T code
    * Removes M105
    * Removes M101
    * Removes M103
    * Replaces M108 with M135

##Architecture
All processors should inherit from the Processor python class in makerbot_driver/GcodeProcessors/.  For processors without strong test coverage, please name them example_ProcessorXYZ. With complete coverage, we will upgrade them to simply ProcessorXYZ.  See tests directory for unit test examples. 

The processor class has only two functions which all inheritors must implement:

###__init__(self)
The main constructor.

###process_gcode(self, gcodes)
The main function for a Processor.  Takes one parameter: a list of gcodes to process.
Returns a list of processed gcodes.

    * @param gcodes: The list of gcodes to process
    * @return output: The processed gcodes
