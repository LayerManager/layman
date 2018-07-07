from flask import jsonify
from .error_list import ERROR_LIST

def error(code_or_message, data=None, http_code=None):
    if isinstance(code_or_message, int):
        code = code_or_message
        message = ERROR_LIST[code_or_message][1]
        if http_code is None:
            http_code = ERROR_LIST[code_or_message][0]
    else:
        code = -1
        message = code_or_message
        if http_code is None:
            http_code = 400

    resp = {'code': code, 'message': message}

    if data is not None:
        resp['data'] = data

    return jsonify(resp), http_code