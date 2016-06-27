'''
Created on Apr 8, 2016

@author: William
'''
import os.path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joule.settings")

from tornado.options import options, define
import django.core.handlers.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
if django.VERSION[1] > 5:
    django.setup()

import tornado_sockets.urls

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

def main():
    settings = {
        "cookie_secret":"k+IsuNhvAjanlxg4Q5cV3fPgAw284Ev7fF7QzvYi1Yw=",
        "template_path":os.path.join(os.path.dirname(__file__), "templates"),
        "static_path":os.path.join(os.path.dirname(__file__), "static"),
        #"xsrf_cookies":True,
        "debug":options.debug,
    }
    
    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
    tornado_app = tornado.web.Application(
        tornado_sockets.urls.urlpatterns
        +[('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),],
        **settings
        )
    
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
    
if __name__ == "__main__":
    main()