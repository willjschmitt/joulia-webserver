"""Main entry point for running the webserver.
"""
import os.path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joulia.settings")

import logging
import django
if django.VERSION[1] > 5:
    django.setup()
import django.core.handlers.wsgi
import tornado.httpserver
import tornado.ioloop
from tornado.options import options, define
import tornado.web
import tornado.wsgi

import tornado_sockets.urls


define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def main():
    LOGGER.info("Starting Joulia server on port %d.", options.port)
    tornado_app = joulia_app()
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


def joulia_app():
    settings = {
        # TODO(willjschmitt): This should be an environment variable in prod.
        "cookie_secret": "k+IsuNhvAjanlxg4Q5cV3fPgAw284Ev7fF7QzvYi1Yw=",
        "debug": options.debug,
    }

    wsgi_app = tornado.wsgi.WSGIContainer(
        django.core.handlers.wsgi.WSGIHandler())
    tornado_app = tornado.web.Application(
        [(r'/', HealthCheckHandler)]
        + tornado_sockets.urls.urlpatterns
        + [('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app))],
        **settings
    )

    return tornado_app


class HealthCheckHandler(tornado.web.RequestHandler):
    """A simple handler to return 200 status for health checks."""

    def get(self):
        self.write("Hello, world")


if __name__ == "__main__":
    main()
