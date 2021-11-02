"""This file contains API configurations."""

from enum import Enum

PROTOCOL = "https://"
DOMAIN = "openstreetcam.org"
VERSION = "1.0"


class OSCAPISubDomain(Enum):
    """This is an enumeration of sub domains.
    Default sub domain is PRODUCTION."""
    PRODUCTION = 'api.'
    TESTING = 'testing-api.'
    STAGING = 'staging-api.'
    BETA = 'beta-api.'
