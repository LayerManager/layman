_ERROR_LIST = {
    1: 'Invalid SLD file',
}


# pylint: disable=super-init-not-called
class Error(Exception):

    def __init__(self, code_or_message, data=None,):
        # Exception.__init__(self)

        self.data = data
        if isinstance(code_or_message, int):
            self.code = code_or_message
            self.message = _ERROR_LIST[code_or_message][1]
        else:
            self.code = -1
            self.message = code_or_message

    def __str__(self):
        return f'Geoserver Error code={self.code} message={self.message} data={self.data}'

    def to_dict(self):
        resp = {'code': self.code, 'message': self.message}
        if self.data is not None:
            resp['detail'] = self.data
        return resp
