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
import tornado.escape as escape
from tornado.options import define, options
import os
import sqlite3 as db
#27017
define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/([a-zA-Z0-9\+]+)/", GlobalLocaleHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", TopicHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", LocalesHandler),
            (r"/view", ViewHandler),
        ]
        
        settings = dict(
        	xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings) 


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
    	http = tornado.httpclient.AsyncHTTPClient()
    	http.fetch("http://localhost:9999/view/categories", callback=self.on_response)	
    def on_response(self, response):
		if response.error: self.finish("avi fucked up")
		globtops = eval(response.body)
		self.render('static/templates/index.html', globtops=globtops)
		

class ViewHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
    	name = self.request.arguments['name'][0]
    	print name
    	http = tornado.httpclient.AsyncHTTPClient()
    	http.fetch("http://localhost:9999/view/category/" + name, callback=self.on_response)
    def on_response(self, response):
    	if response.error: self.finish("avi fucked up")
    	self.finish(response.body)


class GlobalLocaleHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + topic, callback=self.on_response)
    def on_response(self, response):
        if response.error: self.finish("avi fucked up")
        print response.body
        json = escape.json_decode(response.body)
        parent = json['parent'][0]
        children = json['children']
        glob_topic = os.path.split(response.request.url)[1]
        self.render("static/templates/glob_locale.html", globlocales=children, glob_topic=glob_topic)


class TopicHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + global_topic + "/" + global_locale , callback=self.on_response)
    def on_response(self, response):
        print response.request.url
        json = escape.json_decode(response.body)
        parent = json['parent']
        topics = json['children']
        glob_locale = os.path.split(response.request.url)[1]
        glob_topic = os.path.split(os.path.split(response.request.url)[0])[1]
        print glob_topic, glob_locale
        self.render("static/templates/topic.html", glob_locale=glob_locale, glob_topic=glob_topic, topics=topics)
        
        
class LocalesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + global_topic + "/" + global_locale + "/" + topic , callback=self.on_response)        
    def on_response(self, response):
        json = escape.json_decode(response.body)
        glob_topic = json['parent']
        locales = json['children']
        topic = os.path.split(response.request.url)[1]
        global_locale = os.path.split(os.path.split(response.request.url)[0])[1]
        self.render('static/templates/locale.html', glob_locale = global_locale, topic = topic, glob_topic = glob_topic, locales = locales)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
if __name__ == "__main__":
    main()