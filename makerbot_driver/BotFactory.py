from __future__ import absolute_import, print_function

import os

import makerbot_driver


class ReturnObject(object):

    def __init__(self):
        pass


class BotFactory(object):
    """This class is a factory for building bot drivers from
    a port connection. This class will take a connection, query it
    to verify it is a geunine 3d printer (or other device we can control)
    and build the appropritae bot type/version/etc from that.
    """
    def __init__(self, profile_dir=None):
        if profile_dir:
            self.profile_dir = profile_dir
        else:
            self.profile_dir = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), 'profiles',)

    def create_inquisitor(self, portname):
        """
        This is made to ameliorate testing, this having to
        assign internal objects with <obj>.<internal_obj> = <obj> is a
        pain.
        """
        return BotInquisitor(portname)

    def build_from_port(self, portname, leaveOpen=True):
        """
        Returns a tuple of an (s3gObj, ProfileObj)
        for a bot at port portname
        """
        botInquisitor = self.create_inquisitor(portname)
        s3gBot, bot_setup_dict = botInquisitor.query(leaveOpen)

        profile_regex = self.get_profile_regex(bot_setup_dict)
        matches = makerbot_driver.search_profiles_with_regex(
            profile_regex, self.profile_dir)
        matches = list(matches)
        return_object = ReturnObject
        attrs = ['s3g', 'profile', 'gcodeparser']
        for a in attrs:
            setattr(return_object, a, None)
        if len(matches) > 0:
            bestProfile = matches[0]
            setattr(return_object, 's3g', s3gBot)
            setattr(return_object, 'profile', makerbot_driver.Profile(bestProfile, self.profile_dir))
            parser = makerbot_driver.Gcode.GcodeParser()
            parser.s3g = s3gBot
            parser.state.profile = getattr(return_object, 'profile')
            setattr(return_object, 'gcodeparser', parser)
        return return_object

    def create_s3g(self, portname):
        """
        This is made to ameliorate testing.  Otherwise we would
        not be able to reliably test the build_from_port function
        w/o being permanently attached to a specific port.
        """
        return makerbot_driver.s3g.from_filename(portname)

    def get_profile_regex(self, bot_setup_dict):
        """
        Decision tree for bot machine decisions.

        @param dict bot_setup_dict: A dictionary containing
          information about the connected bot
        @return str
        """
        regex = None
        #First check for VID/PID matches
        if 'vid' in bot_setup_dict and 'pid' in bot_setup_dict:
            regex = self.get_profile_regex_has_vid_pid(bot_setup_dict)
        if regex and bot_setup_dict.get('tool_count', 0) == 1:
            regex = regex + 'Single'
        elif regex and bot_setup_dict.get('tool_count', 0) == 2:
            regex = regex + 'Dual'
        return regex

    def get_profile_regex_has_vid_pid(self, bot_setup_dict):
        """If the machine has a VID and PID, we can assume it is part of
        the generation of machines that also have a tool_count.  We use the
        tool_count at the final criterion to narrow our search.
        """
        vid_pid_matches = []
        for bot in makerbot_driver.g_botClasses().values():
            if bot['vid'] == bot_setup_dict['vid'] and bot['pid'] == bot_setup_dict['pid']:
                return bot['botProfiles']
        return None


class BotInquisitor(object):
    def __init__(self, portname):
        """ build a bot Inqusitor for an exact port"""
        self._portname = portname

    def create_s3g(self):
        """
        This is made to ameliorate testing, this having to
        assign internal objects with <obj>.<internal_obj> = <obj> is a
        pain.
        """
        return makerbot_driver.s3g.from_filename(self._portname)

    def query(self, leaveOpen=True):
        """ open a connection to a bot and  query a bot for
            key settings needed to construct a bot from a profile
            @param leaveOpen IF true, serial connection to the bot is left open.
            @return a tuple of an (s3gObj, dictOfSettings"""
        import makerbot_driver.s3g as s3g
        import uuid
        settings = {}
        s3gDriver = self.create_s3g()
        settings['fw_version'] = s3gDriver.get_version()
        if settings['fw_version'] >= 500:
            settings['tool_count'] = s3gDriver.get_toolhead_count()
            settings['vid'], settings['pid'] = s3gDriver.get_vid_pid()
            settings['verified_status'] = s3gDriver.get_verified_status()
            settings['proper_name'] = s3gDriver.get_name()
            #Generate random UUID
            settings['uuid'] = uuid.uuid4()
        if settings['fw_version'] >= makerbot_driver.x3g_minimum_version:
            s3gDriver.set_print_to_file_type('x3g')
        if not leaveOpen:
            s3gDriver.close()

        return s3gDriver, settings
