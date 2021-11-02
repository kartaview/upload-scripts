"""This script is used to get osm authentication token and secret token."""
from typing import Tuple, Optional

from requests_oauthlib import OAuth1Session


def __osm_auth_service() -> OAuth1Session:
    """Factory method that builds osm auth service"""
    oauth = OAuth1Session(client_key='rBWV8Eaottv44tXfdLofdNvVemHOL62Lsutpb9tw',
                          client_secret='rpmeZIp49sEjjcz91X9dsY0vD1PpEduixuPy8T6S')
    return oauth


def osm_auth(request_user_action, error_handle) -> Tuple[Optional[str], Optional[str]]:
    service = __osm_auth_service()
    service.fetch_request_token('https://www.openstreetmap.org/oauth/request_token')
    authorization_url = service.authorization_url('https://www.openstreetmap.org/oauth/authorize')
    request_user_action(authorization_url)
    # pylint: disable=W0703
    try:
        access_token_url = 'https://www.openstreetmap.org/oauth/access_token'
        access_token_response = service.fetch_access_token(access_token_url,
                                                           verifier=" ")
    except Exception as ex:
        error_handle(ex)
        return None, None

    return access_token_response['oauth_token'], access_token_response['oauth_token_secret']
