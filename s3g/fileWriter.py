"""An implementation of s3g that writes s3g packets to a file.

Due to the nature of building to file, we cannot handle ANY Query commands.  Thus,
if a user tries to write a query command to file, we throw a AttemptedQueryCommand error.
"""

from s3g import *

class s3gFileWriter(s3g):

  def BuildAndSendQueryPayload(self, *args):
    raise AttemptedQueryCommand
  
  def SendCommand(self, payload):
    self.file.write(payload)
