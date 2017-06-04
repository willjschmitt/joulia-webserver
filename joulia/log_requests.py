"""Forked from https://gist.github.com/Suor/7870909. Used for logging the
headers of a request for debugging things like authentication behind proxies.
"""

import re
from http.client import responses
import logging

req_log = logging.getLogger(__name__)


def log_cond(request):
    return re.search(r'^/(login|logout|auth)', request.path)


class HeadersLoggingMiddleware(object):
    def process_response(self, request, response):
        if log_cond(request):
            keys = sorted(
                filter(
                    lambda k: re.match(r'(HTTP_|CONTENT_)', k), request.META))
            keys = ['REMOTE_ADDR'] + keys
            meta = ''.join("%s=%s\n" % (k, request.META[k]) for k in keys)

            try:
                status_text = responses[response.status_code]
            except KeyError:
                status_text = 'UNKNOWN STATUS CODE'
            status = '%s %s' % (response.status_code, status_text)
            response_headers = [(str(k), str(v)) for k, v in response.items()]
            for c in response.cookies.values():
                response_headers.append(
                    ('Set-Cookie', str(c.output(header=''))))
            headers = ''.join("%s: %s\n" % c for c in response_headers)
            req_log.info('"%s %s\n%s\n%s\n%s' % (request.method,
                                                 request.build_absolute_uri(),
                                                 meta, status, headers))
        return response
