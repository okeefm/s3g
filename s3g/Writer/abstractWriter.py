class AbstractWriter(object):

  def SendActionPayload(self, payload):
    """ Send the given payload as an action command

    @param bytearray payload Payload to send as an action payload
    """
    raise NotImplementedError()

  def SendQueryPayload(self, payload):
    """ Send the given payload as a query command
    
    @param bytearray payload Payload to send as a query packey
    @return The packet returned by SendCommand
    """
    raise NotImplementedError()

