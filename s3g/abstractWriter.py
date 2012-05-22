
class abstractWriter(object):

  def BuildAndSendActionPayload(self, *args):
    """
    Given a set of parameters, puts them into a bytearray and send them off using SendCommand

    @param *args A set of arguments to put inside a bytearray
    """
    raise NotImplementedError()

  def BuildAndSendQueryPayload(self, *args):
    """Given a set of parameters, puts them into a bytearray and sends them off using Sendcommand.
    
    @param *args A set of arguments to put inside a bytearray
    @return The packet returned by SendCommand
    """
    raise NotImplementedError()

  def SendCommand(self, *args):
    """Given a set of parameters, puts them into a bytearray and sends them off using Sendcommand.
    
    @param *args A set of arguments to put inside a bytearray
    @return The packet returned by SendCommand
    """
    raise NotImplementedError()
