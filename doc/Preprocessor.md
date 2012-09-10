#Preprocessor
There are many flavors of gcode created by many programs.  To keep makerbot_driver manageable, we can only handle a subset of those commands well.  In order to allow greater compatiblity, makerbot_driver has a set of preprocessors to convert many common gcode flavors into a gcode twhich makerbot_driver can easily use. 

##Adding Preprocessors
e encourage users to add preprocessors of their own into s3g.  We will accept any preprocessor with 'example_' as a name, with or without tests.  We will only accept as preprocessor as'PreProcessorX' if it has excellent unit test coverage, comparbile to otuer PreProcessors.


##List of Preprocessors
We have provided an array of common Preprocessors for older MakerBot variants of gcode, as well as some common slicing engines.

###Preprocessor
An interface that all preprocessors inherit from.

###Skeinforge 50 Preprocessor
A preprocessor that is meant to be run on a .gcode file skeined by skeinforge-50 WITHOUT start and end gcodes.

    * Removes M104 commands if they do not include a T code
    * Removes M105
    * Removes M101
    * Removes M103
    * Replaces M108 with M135

##Architecture
All preprocessors should inherit from the Preprocessor python class in makerbot_driver/Preprocessors/.  For processors without strong test coverage, please name them example_PreProcessorXYZ. With complete coverage, we will upgrade them to simply PreProcessorXYZ.  See tests directory for unit test examples. 

The preprocessor class has only two functions which all inheritors must implement:

###__init__(self)
The main constructor.

###process_file(self, input_path, output_path)
The main function for a Preprocessor.  Takes two parameters, an input_path and an output_path.

    * input_path: The filepath to the gcode file that needes to get processed
    * output_path: The filepath to the soon-to-be processed gcode file


