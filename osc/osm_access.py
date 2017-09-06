import http.cookiejar
import os
import urllib.request, urllib.error, urllib.parse
from rauth import OAuth1Service
import sys
from osc.osc_actions import get_osc_login


def get_osm():
    osm = OAuth1Service(
        name='openstreetmap',
        consumer_key='rBWV8Eaottv44tXfdLofdNvVemHOL62Lsutpb9tw',
        consumer_secret='rpmeZIp49sEjjcz91X9dsY0vD1PpEduixuPy8T6S',
        request_token_url='http://www.openstreetmap.org/oauth/request_token',
        access_token_url='http://www.openstreetmap.org/oauth/access_token',
        authorize_url='http://www.openstreetmap.org/oauth/authorize',
        signature_obj='',
        base_url='http://www.openstreetmap.org/')
    return osm


def get_osm_oauth(osm):
    request_token, request_token_secret = osm.get_request_token()
    authorize_url = osm.get_authorize_url(request_token)
    print("")
    print('For login go to this URL in your browser:')
    print(authorize_url)
    print((input("Login and  grant acces then press ENTER")))
    cj = http.cookiejar.CookieJar()
    cookies = [{
        "name": "",
        "value": "",
        "domain": "domain",
        "path": "path",
        "secure": "secure",
    }]
    for cookie in cookies:
        c = http.cookiejar.Cookie(version=1,
                                  name=cookie["name"],
                                  value=cookie["value"],
                                  port=None,
                                  port_specified=False,
                                  domain=cookie["domain"],
                                  domain_specified=False,
                                  domain_initial_dot=False,
                                  path=cookie["path"],
                                  path_specified=True,
                                  secure=cookie["secure"],
                                  expires=None,
                                  discard=True,
                                  comment=None,
                                  comment_url=None,
                                  rest={'HttpOnly': None},
                                  rfc2109=False)
        cj.set_cookie(c)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        opener.open(urllib.request.Request(authorize_url))
    except urllib.error.HTTPError as e:
        print("Can't get osm id")
        print(
            "Please retry and report this issue with the error code on https://github.com/openstreetview/uploader")
        print(e.code)
        print(e.read())
        print(e)
        sys.exit()
    pin = cj._cookies['www.openstreetmap.org']['/']['_osm_session'].value

    return request_token, request_token_secret, pin


def get_access_token(url_access):
    if os.path.isfile("access_token.txt"):
        token_file = open("access_token.txt", "r+")
        string = token_file.read()
        access_token = string
    else:
        osm = get_osm()
        request_token, request_token_secret, pin = get_osm_oauth(osm)
        get_osc_login(url_access, osm, request_token, request_token_secret, pin)
        token_file = open("access_token.txt", "r+")
        string = token_file.read()
        access_token = string
    return access_token