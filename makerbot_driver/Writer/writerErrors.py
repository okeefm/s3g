class ExternalStopError(Exception):
    """
    An ExternalStopError is thrown when an external
    source wishes to force the StreamWriter to stop
    sending packets to a stream.
    """


class NonBinaryModeFileError(IOError):
    """
    A NonBinaryModeFileError is raised when a file is
    passed into FileWriter that is not opened in
    binary mode.  Open a binary mode file with 'wb'
    """
