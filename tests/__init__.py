from collections import namedtuple

Action = namedtuple('ActionTypeDef', ['method', 'params', ])
Publication = namedtuple('PublicationTypeDef', ['workspace', 'type', 'name'])
