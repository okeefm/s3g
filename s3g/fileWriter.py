"""An implementation of s3g that writes s3g packets to a file.

Due to the nature of building to file, we cannot handle ANY Query commands.  Thus,
if a user tries to write a query command to file, we throw a AttemptedQueryCommand error.
"""

from abstractWriter import *
from s3g import *

class FileWriter(AbstractWriter):
  """ A file writer can be used to export an s3g payload stream to a file
  """
    
  def __init__(self, file):
    """ Initialize a new file writer

    @param string file File object to write to.
    """
    self.file = file

  def BuildAndSendActionPayload(self, *args):
    payload = BuildPayload(args)
    self.file.write(bytes(payload))

