#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Hunter Lang and Avi Romanoff
# AGPL 3 License. See LICENSE.
from tornado.options import define, options
import tornado.template as template
from tornado.escape import json_encode
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import pymongo

define("port", default=9999, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        obj_id_regex = r"[a-z0-9]+"
        handlers = [
            (r"/gcdifn/([A-Za-z0-9\-\.\_]+)", GetCategoryIdFromName),
            (r"/view/category/([A-Za-z0-9\-\.\_]+)", ViewCategoryHandler),
            (r"/edit/category/([A-Za-z0-9\-\.\_]+)", EditCategoryHandler),
        ]
        
        settings = dict(
            debug : True,
        )
        tornado.web.Application.__init__(self, handlers, **settings) 

class GetCategoryIdFromName(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, name):
        self.finish([{'name' : name, 'id' : '4de6abd5da558a49fc5eef29'}])

class ViewCategoryHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, foo):
		self.finish([{'bite_me' : True}])

class EditCategoryHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, foo):
		self.finish([{'bite_me' : True}])

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
