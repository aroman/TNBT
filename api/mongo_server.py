#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Hunter Lang and Avi Romanoff
# AGPL 3 License. See LICENSE.
from tornado.options import define, options
from tornado.escape import json_encode
import tornado.template as template
import tornado.escape as escape
import tornado.httpserver
import tornado.options
import tornado.ioloop
import tornado.web
from pprint import pprint as pp
from pymongo import Connection
import logging
import uuid

import fixtures

define("port", default=9999, help="run on the given port", type=int)

MONGO_SERVER = "localhost"
MONGO_PORT = 27017

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/add/comment", AddCommentHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)", ViewGlobalLocalesHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewTopicsHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewLocalesHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewIssuesHandler),
            (r"/view/categories", ViewCategoriesHandler),
        ]
        
        settings = {
            "debug" : True, # For auto-reload
        }
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    connection = Connection(MONGO_SERVER, MONGO_PORT)
    db = connection['struts_server']
    categories = db['categories']

    
    # Currently down to tier-3
    """
    categories.drop()
    for global_topic in fixtures.global_topics:
        global_locales = []
        for global_locale in fixtures.global_locales:
            if global_topic is "Environment":
                topics = [{'name' : "Pollution"}, {'name' : "Global Warming"}, {'name' : "Natural Resources"}, {'name' : "Waste Management"}]
            else:
                topics = []
            global_locales.append({'name' : global_locale, 'topics' : topics})
        categories.insert({'name' : global_topic, 'children' : global_locales})

    for x in categories.find(): pp(x)
    """

class AddCommentHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        db = self.db
        body = self.request.arguments['body'][0]
        _id = str(uuid.uuid4())
        discussion_id = self.request.arguments['discussion_id'][0]
        author = self.request.arguments['author'][0]
        if author == "None": author = "Anonymous"
        db.execute('insert into comment values (?,?,?,?)', [unicode(body, 'utf-8'), unicode(_id, 'utf-8'), unicode(discussion_id, 'utf-8'), unicode(author, 'utf-8')])
        self.dbc.commit()
        print "Hey."
        comment = {
            "_id": _id,
            "author": author,
            "body": body,
            "discussion_id": discussion_id
        }
        self.new_comments([comment])
        self.finish(comment)

class ViewGlobalLocalesHandler(BaseHandler):
    @tornado.web.asynchronous

    def get(self, global_topic):
        results = []
        for child in self.categories.find_one({'name' : global_topic})['children']:
            results.append(child['name'])
        finish = {
            "parent" : global_topic,
            "children" : results,
        }
        self.finish(finish)

class ViewTopicsHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale):
        db = self.db
        db.execute('select _id from global_topic where name = ?', [global_topic])
        topic_id = db.fetchone()[0]
        db.execute('select _id from global_locale where parent_id = ? and name = ?', [topic_id, global_locale])
        locale_id = db.fetchone()[0]
        db.execute('select name from topic where parent_id = ?', [locale_id])
        topics = db.fetchall()
        finish = {
            "parent": global_topic,
            "children": topics
        }
        
        self.finish(finish)

#    def get(self, global_topic, global_locale):
#        results = []
#        for child in self.categories.find_one({'name' : global_topic, 'children' : })['children']:
#            results.append(child)
#        finish = {
#            "parent" : global_topic,
#            "children" : results
#        }
#        finish = {
#            "parent": global_topic,
#            "children": topics
#        }
        
#        self.finish(finish)

class ViewLocalesHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale, topic):
        db = self.db
        db.execute('select _id from global_topic where name = ?', [global_topic])
        topic_id = db.fetchone()[0]
        db.execute('select _id from global_locale where parent_id = ? and name = ?', [topic_id, global_locale])
        locale_id = db.fetchone()[0]
        db.execute('select _id from topic where parent_id = ? and name = ?', [locale_id, topic])
        topic_id = db.fetchone()[0]
        db.execute('select name from locale where parent_id = ?', [topic_id])
        locales = db.fetchall()
        db.execute('select discussion_id from topic where _id = ?', [topic_id])
        discussion = db.fetchone()[0]
        db.execute('select body, author, _id from comment where discussion_id = ?', [discussion])
        comments = db.fetchall()
        finish = {
            "parent": global_topic,
            "children": locales,
            "comments": comments,
            "discussion_id": discussion
        }
        
        self.finish(finish)

class ViewIssuesHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale, topic, locale):
        db = self.db
        db.execute('select _id from global_topic where name = ?', [global_topic])
        topic_id = db.fetchone()[0]
        db.execute('select _id from global_locale where parent_id = ? and name = ?', [topic_id, global_locale])
        locale_id = db.fetchone()[0]
        db.execute('select _id from topic where parent_id = ? and name = ?', [locale_id, topic])
        topic_id = db.fetchone()[0]
        db.execute('select _id from locale where parent_id = ? and name = ?', [topic_id, locale])
        locale_id = db.fetchone()[0]
        db.execute('select _id from issue where parent_id = ?', [locale_id])
        issues = db.fetchall()
        db.execute('select discussion_id from locale where _id = ?', [locale_id])
        discussion = db.fetchone()[0]
        db.execute('select body, author, _id from comment where discussion_id = ?', [discussion])
        comments = db.fetchall()
        finish = {
            "parent": global_topic,
            "children": issues,
            "comments": comments,
            "discussion_id": discussion
        }
        
        self.finish(finish)

class ViewCategoriesHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        results = []
        for global_topic in self.categories.find():
            results.append(global_topic['name'])
        pp(results)
        self.finish(str(results))

def main():
    tornado.options.parse_command_line()
    logging.info("API server starting up") 
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    logging.info("Serving on port %i" % options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
