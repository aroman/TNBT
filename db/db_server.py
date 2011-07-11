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
        handlers = [
            (r"/gcdifn/([A-Za-z0-9\-\.\_]+)", GetCategoryIdFromName),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)", ViewChildrenHandler),
            (r"/view/categories", ViewCategoriesHandler),
            (r"/view/category/([A-Za-z0-9\-\.\_]+)", ViewCategoryHandler),
            (r"/edit/category/([A-Za-z0-9\-\.\_]+)", EditCategoryHandler),
        ]
        
        settings = dict(
            debug= True,
        )
        tornado.web.Application.__init__(self, handlers, **settings) 

class ViewChildrenHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, raw):
        splits = raw.split('|')
        try:
            parent_name = splits[0]
            child_name = splits[1]
        except:
            self.finish("You forgot the pipe, dumbass.")
        results = {"parent" : "", "children" : []}
        try:
            parent = global_topics.find_one({"name" : parent_name})
            results["parent"] = parent["name"]
            for child in parent["children"][0]:
                    results["children"].append(child["name"])
        except TypeError:
            results = None
        
        
        self.finish(results)

class ViewCategoriesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        results = []
        for post in global_topics.find():
            results.append(post['name'])
        self.finish(str(results))

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
