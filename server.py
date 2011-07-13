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
import logging
import uuid
import sqlite3 as db
#27017
define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/waitforcomments", WaitForCommentsHandler),
            (r"/comment", NewCommentHandler),
            (r"/([a-zA-Z0-9\+]+)/", GlobalLocaleHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", TopicHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", LocalesHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", IssuesHandler),
            (r"/view", ViewHandler),
        ]
        
        settings = dict(
            debug=True
        )
        tornado.web.Application.__init__(self, handlers, **settings) 


class CommentMixin(object):
    waiters = []
    cache = []
    cache_size = 200
    
    def wait_for_comments(self, callback, discussion_id, cursor=None,):
        cls = CommentMixin
        if cursor:
            index = 0
            for i in xrange(len(cls.cache)):
                index = len(cls.cache) - i - 1
                if cls.cache[index]["id"] == cursor: break
            recent = cls.cache[index + 1:]
            if recent:
                callback(recent)
                return
        cls.waiters.append([callback, discussion_id])

    def new_comments(self, comments):
        cls = CommentMixin
        logging.info("Sending new comment to %r listeners", len(cls.waiters))
        for callback in cls.waiters:
            try:
                comment_list = []
                for comment in comments:
                    if callback[1] == comment["discussion_id"]:
                        comment_list.append(comment)
                callback[0](comment_list)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.waiters = []
        cls.cache.extend(comments)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    
    def get(self):
    	http = tornado.httpclient.AsyncHTTPClient()
    	http.fetch("http://localhost:9999/view/categories", callback=self.on_response)	
    
    def on_response(self, response):
		if response.error: self.finish(response.error)
		globtops = eval(response.body)
		self.render('static/templates/index.html', globtops=globtops)


class NewCommentHandler(tornado.web.RequestHandler, CommentMixin):
    
    def post(self):
        comment = {
            "_id": str(uuid.uuid4()),
            "discussion_id": self.get_argument("discussion_id"),
            "author": "Anonymous",
            "body": self.get_argument("body")
        }
        self.new_comments([comment])


class WaitForCommentsHandler(tornado.web.RequestHandler, CommentMixin):
    @tornado.web.asynchronous
    
    def post(self):
        discussion_id = self.request.arguments['discussion_id'][0]
        cursor = self.get_argument("cursor", None)
        self.wait_for_comments(self.async_callback(self.on_new_comments), discussion_id, cursor=cursor)

    def on_new_comments(self, comments):
        if self.request.connection.stream.closed():
            return 
        self.render('static/templates/comments_only.html', comments=comments)


class ViewHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    
    def post(self):
    	name = self.request.arguments['name'][0]
    	http = tornado.httpclient.AsyncHTTPClient()
    	http.fetch("http://localhost:9999/view/category/" + name, callback=self.on_response)
    
    def on_response(self, response):
    	if response.error: self.finish(response.error)
    	self.finish(response.body)


class GlobalLocaleHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    
    def get(self, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + topic, callback=self.on_response)
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
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
        if response.error: self.finish(response.error)
        json = escape.json_decode(response.body)
        parent = json['parent']
        topics = json['children']
        glob_locale = os.path.split(response.request.url)[1]
        glob_topic = os.path.split(os.path.split(response.request.url)[0])[1]
        self.render("static/templates/topic.html", glob_locale=glob_locale, glob_topic=glob_topic, topics=topics)
        
        
class LocalesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    
    def get(self, global_topic, global_locale, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + global_topic + "/" + global_locale + "/" + topic , callback=self.on_response)        
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
        json = escape.json_decode(response.body)
        glob_topic = json['parent']
        locales = json['children']
        comments = json['comments']
        discussion_id = json["discussion_id"]
        topic = os.path.split(response.request.url)[1]
        global_locale = os.path.split(os.path.split(response.request.url)[0])[1]
        self.render('static/templates/locale.html', glob_locale = global_locale, topic = topic, glob_topic = glob_topic, 
            locales = locales, comments=comments, discussion_id=discussion_id)


class IssuesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    
    def get(self, global_topic, global_locale, topic, locale):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("http://localhost:9999/view/children/" + global_topic + "/" + global_locale + "/" + topic + "/" + locale , 
            callback=self.on_response)        
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
        json = escape.json_decode(response.body)
        glob_topic = json['parent']
        locales = json['children']
        comments = json['comments']
        discussion_id = json["discussion_id"]
        locale = os.path.split(response.request.url)[1]
        topic = os.path.split(os.path.split(response.request.url)[0])[1]
        global_locale = os.path.split(os.path.split(os.path.split(response.request.url)[0])[0])[1]
        self.render('static/templates/locale.html', glob_locale = global_locale, topic = topic, glob_topic = glob_topic,
            locales = locales, comments=comments, discussion_id=discussion_id)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
if __name__ == "__main__":
    main()