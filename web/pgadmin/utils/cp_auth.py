from base64 import b64encode
from Crypto.Hash import SHA,HMAC
from flask import request, Response, abort
from flask.ext.login import current_user
from functools import wraps
import config, os


def create_signature(string_to_sign):
        print 0
        hmac = HMAC.new(config.CP_SSO_SECRET, string_to_sign, SHA)
        print 1
        return b64encode(hmac.hexdigest())

def validate_token(customer_id, key):
        print "See for yourself"
        signed =  create_signature(str(customer_id))
        print key
        print signed
        if key==signed:
                return True
        else:
                return False

def cp_authorized(fn):
    """Decorator that checks that requests
    contain an id-token in the request cookies.
    userid will be None if the
    authentication failed, and have an id otherwise.

    Usage:
    @blueprint.route("/")
    @authorized
    def secured_root(userid=None):
        pass
    """
    @wraps(fn)
    def decorated(*args, **kwargs):
        if config.CP_SSO_COOKIE_NAME not in request.cookies:
            # Unauthorized
            print("No cookie for auth")
            abort(401)
        cookie = request.cookies[config.CP_SSO_COOKIE_NAME]
        cookie_parts = cookie.split()
        temp_user_id =cookie_parts[0].split(':')[1]
        print("Checking token... %s with %s"%(temp_user_id, cookie_parts[1]))
        userid = None
        isValid = validate_token(temp_user_id, cookie_parts[1])
        if isValid:
            userid = temp_user_id
        if userid is None:
            print("Check returned FAIL!")
            # Unauthorized
            abort(401)
            return None
        current_user.id = 1 
        return fn(userid=userid, *args, **kwargs)
    print 'returning'
    return decorated    