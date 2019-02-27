"""This module is responsible with getting access to OSC API"""
import os
import sys
import urllib
import json
import logging
from osm_access import osm_auth
from osc_api_gateway import OSCApi
from osc_api_gateway import OSCUser
from osc_api_gateway import OSCAPISubDomain

# constants
CREDENTIALS_FILE = "credentials.json"
OSM_KEY = "osm"
OSC_KEY = "osc"

TOKEN_KEY = "token"
TOKEN_SECRET_KEY = "token_secret"

OSC_ENV_KEY = "osc_env"
USER_ID_KEY = "user_id"
USER_NAME_KEY = "user_name"
USER_FULL_NAME_KEY = "full_name"

LOGGER = logging.getLogger('osc_tools.logging_controller')


class LoginController:
    """This class will enable """

    def __init__(self, sub_domain: OSCAPISubDomain):
        self.osc_api = OSCApi(sub_domain)
        self.handle_retry_count = 0
        self.user: OSCUser = None
        self.osm_token = ""
        self.osm_token_secret = ""

        osm_token, osm_token_secret, osc_user, env = self.__read_persistent_login()
        self.osm_token = osm_token
        self.osm_token_secret = osm_token_secret
        LOGGER.debug("Current environment: %s Cached environment: %s", str(sub_domain), str(env))
        if env == sub_domain:
            LOGGER.debug("Same environment detected")
            self.user = osc_user

    def login(self) -> OSCUser:
        """This method makes osm authentication and request osc authorization for API usage"""
        if self.user is not None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            LOGGER.info("Logged in user: %s. To log out delete %s/%s",
                        self.user.name,
                        dir_path,
                        CREDENTIALS_FILE)
            return self.user

        if self.osm_token == "" or self.osm_token_secret == "":
            # osm authentication
            LOGGER.debug("Will start osm auth")
            osm_token, osm_secret = osm_auth(self.__prompt_user_for_login,
                                             self.__handle_osm_auth_error)
            LOGGER.debug("OSM auth done")
            if osm_token is None or osm_secret is None:
                LOGGER.debug("osm auth failed will retry")
                # retry login process. this happens just once.
                return self.login()

            self.__persist_login(osm_token=osm_token, osm_secret=osm_secret)
            self.osm_token = osm_token
            self.osm_token_secret = osm_secret

        # osc authorization
        osc_user, exception = self.osc_api.authorized_user("osm",
                                                           self.osm_token,
                                                           self.osm_token_secret)
        if exception is not None:
            self.__handle_error_on_authorization(exception)

        self.__persist_login(osc_user=osc_user)
        self.user = osc_user

        return osc_user

    @classmethod
    def logout(cls):
        """This method will remove the previously cached credentials"""
        os.remove(CREDENTIALS_FILE)

    def __handle_osm_auth_error(self, error: Exception):
        if isinstance(error, urllib.error.HTTPError):
            LOGGER.warning("Can't get osm id")
            LOGGER.warning("Please report this issue with the error code on "
                           "https://github.com/openstreetcam/upload-scripts")
            LOGGER.warning(error.code)
            LOGGER.warning(error.read())
            sys.exit()
        elif self.handle_retry_count == 0:
            self.handle_retry_count = 1
            LOGGER.warning("An error occurred.")
            LOGGER.debug("Error message: %s", str(error))
            LOGGER.warning("This error can occur when you did not log in your browser. "
                           "Please make sure to follow the next steps to retry.")
        else:
            LOGGER.warning("Error message: %s", str(error))
            LOGGER.warning("Please report this issue with the error message"
                           "https://github.com/openstreetcam/upload-scripts")
            sys.exit()

    @classmethod
    def __prompt_user_for_login(cls, osm_url: str):
        LOGGER.warning("")
        LOGGER.warning('For login go to this URL in your browser:')
        LOGGER.warning(osm_url)
        LOGGER.warning((input("Login and grant access then press ENTER")))

    @classmethod
    def __handle_error_on_authorization(cls, exception: Exception):
        LOGGER.warning("Can't get osc authorization right now please try again "
                       "or if you already did this.")
        LOGGER.warning("Please report this issue with the error message on "
                       "https://github.com/openstreetcam/upload-scripts")
        LOGGER.warning(exception)
        sys.exit()

    def __persist_login(self, osm_token: str = "", osm_secret: str = "", osc_user: OSCUser = None):
        LOGGER.debug("will save credentials into file")
        # read the cached values from json file
        old_osm_token, old_osm_secret, old_user, old_environment = self.__read_persistent_login()
        # update the json file with the new values
        # if value is missing just use the old value

        credentials_dict = {}

        # validate osm credentials
        if osm_token == "" or osm_secret == "" and old_osm_token != "" and old_osm_secret != "":
            LOGGER.debug("using cached osm credentials")
            osm_token = old_osm_token
            osm_secret = old_osm_secret

        if osm_token != "" and osm_secret != "":
            LOGGER.debug("prepare to write osm credentials")
            credentials_dict[OSM_KEY] = {TOKEN_KEY: osm_token,
                                         TOKEN_SECRET_KEY: osm_secret}
        # validate osc credentials
        osc_env = self.osc_api.environment
        if osc_user is None and \
                old_user is not None and \
                self.osc_api.environment == old_environment:
            LOGGER.debug("using cached osc user")
            osc_user = old_user

        if osc_user is not None:
            LOGGER.debug("prepare to write osc user")
            credentials_dict[OSC_KEY] = {USER_ID_KEY: osc_user.user_id,
                                         USER_NAME_KEY: osc_user.name,
                                         USER_FULL_NAME_KEY: osc_user.full_name,
                                         TOKEN_KEY: osc_user.access_token,
                                         OSC_ENV_KEY: osc_env.value}
        with open(CREDENTIALS_FILE, 'w') as output:
            json.dump(credentials_dict, output)
            LOGGER.debug("Did write data to credentials file")

    @classmethod
    def __read_persistent_login(cls) -> (str, str, OSCUser, OSCAPISubDomain):
        LOGGER.debug("will read credentials file")
        try:
            with open(CREDENTIALS_FILE) as json_file:
                data = json.load(json_file)
                osc_user: OSCUser = None
                environment: OSCAPISubDomain = None
                if OSC_KEY in data:
                    osc_data = data[OSC_KEY]
                    if USER_NAME_KEY in osc_data and \
                            USER_ID_KEY in osc_data and \
                            USER_FULL_NAME_KEY in osc_data and \
                            OSC_ENV_KEY in osc_data and \
                            TOKEN_KEY in osc_data:
                        LOGGER.debug("OSC User found in credentials file")
                        osc_user = OSCUser()
                        osc_user.user_id = osc_data[USER_ID_KEY]
                        osc_user.name = osc_data[USER_NAME_KEY]
                        osc_user.full_name = osc_data[USER_FULL_NAME_KEY]
                        osc_user.access_token = osc_data[TOKEN_KEY]
                        environment = OSCAPISubDomain(osc_data[OSC_ENV_KEY])

                osm_token = ""
                osm_token_secret = ""
                if OSM_KEY in data:
                    osm_data = data[OSM_KEY]
                    if TOKEN_KEY in osm_data and TOKEN_SECRET_KEY in osm_data:
                        LOGGER.debug("OSM User found in credentials file")
                        osm_token = osm_data[TOKEN_KEY]
                        osm_token_secret = osm_data[TOKEN_SECRET_KEY]

                return osm_token, osm_token_secret, osc_user, environment
        except FileNotFoundError:
            LOGGER.debug("No file credentials file found")
            return "", "", None, None
