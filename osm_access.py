"""This script is used to get osm authentication token and secret token."""
from rauth import OAuth1Service


def __osm_auth_service() -> OAuth1Service:
    """Factory method that builds osm auth service"""
    osm = OAuth1Service(
        name='openstreetmap',
        consumer_key='rBWV8Eaottv44tXfdLofdNvVemHOL62Lsutpb9tw',
        consumer_secret='rpmeZIp49sEjjcz91X9dsY0vD1PpEduixuPy8T6S',
        request_token_url='https://www.openstreetmap.org/oauth/request_token',
        access_token_url='https://www.openstreetmap.org/oauth/access_token',
        authorize_url='https://www.openstreetmap.org/oauth/authorize',
        signature_obj='',
        base_url='https://www.openstreetmap.org/')
    return osm


def osm_auth(request_user_action, error_handle) -> (str, str):
    """OSM authentication calls are made here. This method receives as parameter
    two functions. First one will be called prior to the parsing of the cookie.
    Second one will be called when some error occurs"""
    auth_service = __osm_auth_service()
    request_token, request_token_secret = auth_service.get_request_token()
    authorize_url = auth_service.get_authorize_url(request_token)
    # user action is required
    request_user_action(authorize_url)

    try:
        session = auth_service.get_auth_session(request_token, request_token_secret)
    except Exception as ex:
        error_handle(ex)
        return None, None

    return session.access_token, session.access_token_secret
