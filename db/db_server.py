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
from pymongo import Connection

define("port", default=9999, help="run on the given port", type=int)
connection = Connection('localhost', 27017)
db = connection['struts_server']
global_topics = db['global-topic']
global_locales = db['global-locales']

class Application(tornado.web.Application):
    def __init__(self):
        obj_id_regex = r"[a-z0img-9]+"
        handlers = [
            (r"/gcdifn/([A-Za-z0-9\-\.\_]+)", GetCategoryIdFromName),
            (r"/view/categories", ViewCategoriesHandler),
            (r"/view/category/([A-Za-z0-9\-\.\_]+)", ViewCategoryHandler),
            (r"/edit/category/([A-Za-z0-9\-\.\_]+)", EditCategoryHandler),
        ]
        
        settings = dict(
            debug= True,
        )
        tornado.web.Application.__init__(self, handlers, **settings) 

class ViewCategoriesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        poverty = {'name' : "Poverty", 'hunterfuckedup' : True}
        global_topics.insert(poverty)
        toppings = global_topics.find()
        fuckups = []
        for post in global_topics.find():
            str(fuckups.append(post['name']))
        self.finish(str(fuckups))

class GetCategoryIdFromName(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, name):
        self.finish(str([{'name' : name, 'id' : '4de6abd5da558a49fc5eef29'}]))

class ViewCategoryHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, foo):
		self.finish(str([{'bite_me' : True}]))

class EditCategoryHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self, foo):
		self.finish(str([{'bite_me' : True}]))

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
