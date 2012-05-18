"""
A file decoder for an s3g file
"""
from s3gStreamDecoder import s3gStreamDecoder

class s3gFileDecoder(s3gStreamDecoder):

  def ParseNextPacket(self):
    """
    Assuming the file pointer is at the start of a packet, parses that packet and returns the command and parameters associated with that command.

    @param Human readable version of the next s3g packet
    """
    return self.ParseNextPayload()

