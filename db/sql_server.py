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
import tornado.escape as escape
import sqlite3 as dbmod
import uuid

define("port", default=9999, help="run on the given port", type=int)

dbc = dbmod.connect('db.db')
db = dbc.cursor()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)", ViewGlobalLocalesHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewTopicsHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewLocalesHandler),
            (r"/view/children/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)/([A-Za-z0-9\-\.\_\%]+)", ViewIssuesHandler),
            (r"/view/categories", ViewCategoriesHandler),
        ]
        
        settings = dict(
            debug= True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class ViewGlobalLocalesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic):
        db.execute('select _id from global_topic where name = ?', [global_topic])
        topic_id = db.fetchone()[0]
        db.execute('select name from global_locale where parent_id = ?', [topic_id])
        glob_locales = db.fetchall()
        finish = {
            "parent": global_topic,
            "children": glob_locales
        }
        
        self.finish(finish)

class ViewTopicsHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale):

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

class ViewLocalesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale, topic):
        db.execute('select _id from global_topic where name = ?', [global_topic])
        topic_id = db.fetchone()[0]
        db.execute('select _id from global_locale where parent_id = ? and name = ?', [topic_id, global_locale])
        locale_id = db.fetchone()[0]
        db.execute('select _id from topic where parent_id = ? and name = ?', [locale_id, topic])
        topic_id = db.fetchone()[0]
        db.execute('select name from locale where parent_id = ?', [topic_id])
        locales = db.fetchall()
        finish = {
            "parent": global_topic,
            "children": locales
        }
        
        self.finish(finish)
class ViewIssuesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, global_topic, global_locale, topic, locale):
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
        finish = {
            "parent": global_topic,
            "children": issues
        }
        
        self.finish(finish)

class ViewCategoriesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        results = []
        db.execute('select name from global_topic')
        names = db.fetchall()
        for name in names:
            results.append(name[0])
        print results
        self.finish(str(results))

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
