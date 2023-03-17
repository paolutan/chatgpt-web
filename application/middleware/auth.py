import functools
import os
from flask import request, make_response, jsonify


def need_authorization(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        auth_secret_key = os.getenv("AUTH_SECRET_KEY").strip()
        authorization = request.headers.get('Authorization', "")
        authorization = authorization.replace('Bearer ', '').strip()
        if not authorization or authorization != auth_secret_key:
            res = {"message": "'Error: 无访问权限 | No access rights'", "status": "Unauthorized", "data": None}
            return make_response(jsonify(res), 403)
        return func(*args, **kwargs)

    return decorator
