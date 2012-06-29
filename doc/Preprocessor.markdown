#Preprocessor
S3g has support for a preprocessor to run transformations on a gcode file.

##Architecture
All preprocessors should inherit from the Preprocessor python class in s3g/preprocessors.  The preprocessor class has only two functions which all inheritors must implement:

###__init__(self)
The main constructor.

###process_file(self, input_path, output_path)
The main function for a Preprocessor.  Takes two parameters, an input_path and an output_path.

    * input_path: The filepath to the gcode file that needes to get processed
    * output_path: The filepath to the soon-to-be processed gcode file

##Adding Preprocessors
We encourage users to add preprocessors of their own into s3g.  However, extensive unit tests must be written for all functions, or preprocessors will not be included in the s3g package.

##List of Preprocessors
###Preprocessor
An interface that all preprocessors inherit from.
