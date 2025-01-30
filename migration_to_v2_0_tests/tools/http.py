from .error_list import ERROR_LIST


# pylint: disable=super-init-not-called
class LaymanError(Exception):

    def __init__(self, code_or_message, data=None, http_code=None, private_data=None, sub_code=None):
        # Exception.__init__(self)

        self.http_code = http_code
        self.data = data
        if isinstance(code_or_message, int):
            self.code = code_or_message
            self.message = ERROR_LIST[code_or_message][1]
            if http_code is None:
                self.http_code = ERROR_LIST[code_or_message][0]
        else:
            self.code = -1
            self.message = code_or_message
            if http_code is None:
                self.http_code = 400
        self.private_data = private_data
        self.sub_code = sub_code

    def __str__(self):
        return f'LaymanError code={self.code} message={self.message} data={self.data} private_info={self.private_data}'

    def to_dict(self):
        resp = {'code': self.code, 'message': self.message}
        if self.sub_code is not None:
            resp['sub_code'] = self.sub_code

        if self.data is not None:
            resp['detail'] = self.data
        return resp
