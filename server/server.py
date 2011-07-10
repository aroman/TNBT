#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Hunter Lang and Avi Romanoff
# AGPL 3 License. See LICENSE.
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.template as template
from tornado.options import define, options
import os
import sqlite3 as db

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
        ]
        
        settings = dict(

        )
        tornado.web.Application.__init__(self, handlers, **settings) 


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
		self.render('static/templates/index.html')

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
if __name__ == "__main__":
    main()
