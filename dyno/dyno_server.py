#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Hunter Lang and Avi Romanoff
# AGPL 3 License. See LICENSE.
from tornado.options import define, options
import tornado.template as template
import tornado.escape as escape
import tornado.httpclient
import tornado.httpserver
import tornado.options
import tornado.ioloop
import tornado.web
import os
import uuid
import logging
import sqlite3 as db

API_ROOT = "http://localhost:9999"

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/waitforcomments", IndexHandler), # The spinning was killing me - switch to firefox. there's no spinning and it's far less bloated than chrome
            (r"/comment", NewCommentHandler),
            (r"/([a-zA-Z0-9\+]+)/", GlobalLocaleHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", TopicHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", LocalesHandler),
            (r"/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)/", IssuesHandler),
            (r"/view", ViewHandler),
        ]
        
        settings = {
            "debug" : True, # For auto-reload
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
        }
        tornado.web.Application.__init__(self, handlers, **settings) 


class CommentMixin(object):
    """
        Magical unicorn that does magical things.
        This is a serious part of the server. Try not to fuck with it.
        
        See method docstrings below for a real explanation.
    """
    
    waiters = []
    cache = []
    cache_size = 200
    
    """
        This method takes a callback and discussion_id as arguments.
        It is called by WaitForCommentsHandler when a client sends a longpolling request.
        It adds discussion_id and callback, which is a function wrapper, to the waiters queue.
    """
    
    def wait_for_comments(self, callback, discussion_id, cursor=None):
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

    """
        This method takes comments as arguments.
        It is called by NewCommentHandler when a client posts a new comment.
        It iterates through the waiters queue, checking to see if the discussion_id 
        in the queue matches the one in the comment. If it does, this means the server
        has found relevant updates, so it sends them to the given callback.
        
        Boom. magic explained.
    """
    def new_comments(self, comments):
        cls = CommentMixin
        logging.info("Sending new comment to %r listeners", len(cls.waiters))
        for callback in cls.waiters:
            """ 
            the problem with this try statement is that every callback gets called, even if their
            discussion_id doesnt match the one in the comment. they just get sent a blank update. 
            while this isnt really a problem right now, it will definitely be a huge issue 
            scalability-wise, considering every single connection gets updated every single time someone comments.
            I should probably fix that...
            """
            try:
                comment_list = []
                for comment in comments:
                    if callback[1] == comment["discussion_id"]:
                            callback[0]([comment])
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
    	http.fetch(API_ROOT + "/view/categories", callback=self.on_response)	
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
        globtops = eval(response.body)
        self.render('static/templates/index.html', globtops=globtops)


class NewCommentHandler(tornado.web.RequestHandler, CommentMixin):
    """
        Request handler for the creation of new comments.
        
        TODO: make a call to the api that adds comments to mongo
    """
    
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
    #    Handles the longpolling requests. Post arguments include a discussion_id.
    #    This method ensures that the created connection gets updates for the posted
    #    discussion_id only.
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
    	http.fetch(API_ROOT + "/view/category/" + name, callback=self.on_response)
    
    def on_response(self, response):
    	if response.error: self.finish(response.error)
    	self.finish(response.body)


class GlobalLocaleHandler(tornado.web.RequestHandler):
    """
        Request handler for the 2rd tier category, Global Locale.
    """
    @tornado.web.asynchronous
    
    def get(self, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(API_ROOT + "/view/children/" + topic, callback=self.on_response)
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
        json = escape.json_decode(response.body)
        parent = json['parent']
        children = json['children']
        glob_topic = os.path.split(response.request.url)[1]
        self.render("static/templates/glob_locale.html", globlocales=children, glob_topic=glob_topic)


class TopicHandler(tornado.web.RequestHandler):
    """
        Request handler for the 3rd tier category, Topic.
    """
    @tornado.web.asynchronous
    
    def get(self, global_topic, global_locale):
        global_locale = global_locale.replace(" ", "%20") # XXX
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(API_ROOT + "/view/children/" + global_topic + "/" + global_locale , callback=self.on_response)
    
    def on_response(self, response):
        if response.error: self.finish(response.error)
        json = escape.json_decode(response.body)
        parent = json['parent']
        topics = json['children']
        glob_locale = os.path.split(response.request.url)[1]
        glob_topic = os.path.split(os.path.split(response.request.url)[0])[1]
        self.render("static/templates/topic.html", glob_locale=glob_locale, glob_topic=glob_topic, topics=topics)
        
        
class LocalesHandler(tornado.web.RequestHandler):
    """
        Request handler for the 4th tier category, Locale.
    """
    @tornado.web.asynchronous
    
    def get(self, global_topic, global_locale, topic):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(API_ROOT + "/view/children/" + global_topic + "/" + global_locale + "/" + topic , callback=self.on_response)        
    
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
    """
        Request handler for the 5th tier category, Issue.
    """
    @tornado.web.asynchronous

    def get(self, global_topic, global_locale, topic, locale):
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(API_ROOT + "/view/children/" + global_topic + "/" + global_locale + "/" + topic + "/" + locale , 
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
        global_locale = os.path.split(os.path.split(os.path.split(response.request.url)[0])[0])[1] # Yes, i know i could do this differently. but this way is just so cool.
        self.render('static/templates/locale.html', glob_locale = global_locale, topic = topic, glob_topic = glob_topic,
            locales = locales, comments=comments, discussion_id=discussion_id)

def main():
    tornado.options.parse_command_line()
    logging.info("Dyno server starting up") 
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    logging.info("Serving on port %i" % options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
