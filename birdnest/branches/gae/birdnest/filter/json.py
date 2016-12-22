import types
import logging

try:
    import simplejson
except:
    from django.utils import simplejson 

import re
from urllib import quote

from birdnest.filter import remove_html
from birdnest.filter import Filter as _Filter

class Filter(_Filter):
  def error_reason(self, text, reason):
    error = simplejson.loads(text)
    return error['error']

  def error_filter(self, text):
    error = simplejson.loads(text)
    del error['request']
    return simplejson.dumps(error)

class StatusesIncludeImage(Filter):
  def filter(self, text):
    unwanted_status = ['truncated', 'in_reply_to_user_id',
                       'in_reply_to_status_id']
    unwanted_user = ['description', 'followers_count', 'protected',
                     'location']
    statuses = simplejson.loads(text)
    for status in statuses:
      for key in unwanted_status:
        if key in status:
          del status[key]
      for key in unwanted_user:
        if key in status['user']:
          del status['user'][key]
    return simplejson.dumps(statuses)

class StatusesTextOnly(Filter):
  def filter(self, text):
    unwanted_status = ['truncated', 'in_reply_to_user_id',
                       'in_reply_to_status_id']
    unwanted_user = ['description',
                     'statuses_count',
                     'followers_count',
                     'friends_count',
                     'favourites_count',
                     'protected',
                     'location',
                     'time_zone',
                     'url',
                     'notifications',
                     'created_at',
                     'profile_image_url',
                     'profile_sidebar_fill_color',
                     'profile_text_color',
                     'profile_background_color',
                     'profile_link_color',
                     'profile_background_image_url',
                     'profile_background_tile',
                     'profile_sidebar_border_color']
    statuses = simplejson.loads(text)
    for status in statuses:
      for key in unwanted_status:
        if key in status:
          del status[key]
      for key in unwanted_user:
        if key in status['user']:
          del status['user'][key]
      status['source'] = remove_html(status['source'])
    return simplejson.dumps(statuses)

class SingleStatusesIncludeImage(Filter):
  def filter(self, text):
    unwanted_status = ['truncated', 'in_reply_to_user_id',
                       'in_reply_to_status_id']
    unwanted_user = ['description', 'followers_count', 'protected',
                     'location']
    status = simplejson.loads(text)
    for key in unwanted_status:
      if key in status:
        del status[key]
    for key in unwanted_user:
      if key in status['user']:
        del status['user'][key]
    return simplejson.dumps(status)

class SingleStatusesTextOnly(Filter):
  def filter(self, text):
    unwanted_status = ['truncated', 'in_reply_to_user_id',
                       'in_reply_to_status_id']
    unwanted_user = ['description',
                     'statuses_count',
                     'followers_count',
                     'friends_count',
                     'favourites_count',
                     'protected',
                     'location',
                     'time_zone',
                     'url',
                     'notifications',
                     'created_at',
                     'profile_image_url',
                     'profile_sidebar_fill_color',
                     'profile_text_color',
                     'profile_background_color',
                     'profile_link_color',
                     'profile_background_image_url',
                     'profile_background_tile',
                     'profile_sidebar_border_color']
    status = simplejson.loads(text)
    for key in unwanted_status:
      if key in status:
        del status[key]
    for key in unwanted_user:
      if key in status['user']:
        del status['user'][key]
    status['source'] = remove_html(status['source'])
    return simplejson.dumps(status)

class DirectMessageIncludeImage(Filter):
  def filter(self, text):
    directmessages = simplejson.loads(text)
    for dm in directmessages:
      sender = dm['sender']
      recipient = dm['recipient']
      dm['sender']  = dm['recipient'] = {}
      dm['sender']['profile_image_url'] = sender['profile_image_url']
      dm['recipient']['profile_image_url'] = recipient['profile_image_url']
    return simplejson.dumps(directmessages)

class DirectMessageTextOnly(Filter):
  def filter(self, text):
    unwanted_dm = ['sender', 'recipient']
    directmessages = simplejson.loads(text)
    for dm in directmessages:
      for key in unwanted_dm:
        del dm[key]
    return simplejson.dumps(directmessages)

class SingleDirectMessageIncludeImage(Filter):
  def filter(self, text):
    dm = simplejson.loads(text)
    sender = dm['sender']
    recipient = dm['recipient']
    dm['sender']  = dm['recipient'] = {}
    dm['sender']['profile_image_url'] = sender['profile_image_url']
    dm['recipient']['profile_image_url'] = recipient['profile_image_url']
    return simplejson.dumps(dm)


class SingleDirectMessageTextOnly(Filter):
  def filter(self, text):
    unwanted_dm = ['sender', 'recipient']
    dm = simplejson.loads(text)
    for key in unwanted_dm:
        del dm[key]
    return simplejson.dumps(dm)
