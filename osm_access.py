"""This script is used to get osm authentication token and secret token."""
from typing import Tuple, Optional

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import OAuth2Token

OSM_AUTH_URL = 'https://www.openstreetmap.org/oauth2/authorize'
OSM_TOKEN_URL = 'https://www.openstreetmap.org/oauth2/token'

# Credentials dedicated for GitHub community
CLIENT_ID = 'xCDlXoN-gVeXsXMHu8N5VArN4iWBDwuMgZAlf5PlC7c'
CLIENT_SECRET = "UICSTaxQkQsSl-osmcbqd5CXJIak5fvw9BF_F152BeE"


def __osm_auth_service() -> OAuth2Session:
    """Factory method that builds osm auth service"""
    oauth = OAuth2Session(client_id=CLIENT_ID,
                          redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                          scope=["openid", "read_prefs"])
    return oauth


def osm_auth(request_user_action, error_handle) -> Tuple[Optional[str], Optional[str]]:
    service = __osm_auth_service()
    authorization_url, _ = service.authorization_url(OSM_AUTH_URL)
    response = request_user_action(authorization_url)
    # pylint: disable=W0703
    try:
        access_token_response: OAuth2Token = service.fetch_token(OSM_TOKEN_URL,
                                                                 code=response,
                                                                 client_id=CLIENT_ID,
                                                                 client_secret=CLIENT_SECRET)

        return access_token_response.get("access_token"), CLIENT_SECRET
    except Exception as ex:
        error_handle(ex)
        return None, None
