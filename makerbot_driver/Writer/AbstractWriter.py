class AbstractWriter(object):
    def open(self):
        """ Opens the currently set port"""
        raise NotImplementedError()

    def is_open(self):
        """ Fluch of file like objects. """
        raise NotImplementedError()

    def send_action_payload(self, payload):
        """ Send the given payload as an action command

        @param bytearray payload Payload to send as an action payload
        """
        raise NotImplementedError()

    def send_query_payload(self, payload):
        """ Send the given payload as a query command

        @param bytearray payload Payload to send as a query packey
        @return The packet returned by send_command
        """
        raise NotImplementedError()
