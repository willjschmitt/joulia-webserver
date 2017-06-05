"""Forked from https://gist.github.com/Suor/7870909. Used for logging the
headers of a request for debugging things like authentication behind proxies.
"""

from http.client import responses
import logging

LOGGER = logging.getLogger(__name__)


class HeadersLoggingMiddleware(object):
    @staticmethod
    def process_response(request, response):
        try:
            status_text = responses[response.status_code]
        except KeyError:
            status_text = 'UNKNOWN STATUS CODE'
        status = '{} {}'.format(response.status_code, status_text)
        request_string = "{} {} {}".format(request.method, status,
                                           request.build_absolute_uri())

        request_headers = []
        for k, v in sorted(request.META.items()):
            request_headers.append('{}={}'.format(k, v))
        request_headers = '\n'.join(request_headers)

        response_headers = []
        for k, v in sorted(response.items()):
            response_headers.append("{}:{}".format(k, v))
        response_headers = '\n'.join(response_headers)

        cookies = '\n'.join(c.output() for c in response.cookies.values())

        LOGGER.info('"%s\nRequest:\n%s\nResponse:\n%s\nCookies:\n%s',
                    request_string, request_headers, response_headers, cookies)

        return response
