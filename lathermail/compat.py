import sys

IS_PY3 = sys.version_info[0] == 3

if IS_PY3:
    from http.client import NO_CONTENT
    from email import encoders as Encoders
    from urllib.parse import quote, urlencode
    unicode = str
    bytes = bytes
else:
    from email import Encoders
    from httplib import NO_CONTENT
    from urllib import quote, urlencode
    unicode = unicode
    _orig_bytes = bytes
    bytes = lambda s, *a: _orig_bytes(s)
