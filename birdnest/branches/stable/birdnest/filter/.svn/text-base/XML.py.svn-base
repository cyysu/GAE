import types
import logging
from xml.etree import ElementTree as ET
from birdnest.filter import Filter as _Filter

class Filter(_Filter):
  def error_reason(self, text, reason):
    return reason

  def error_filter(self, text):
    return text

def copy_element(builder, source, tag):
  builder.start(tag, {})
  builder.data(source.findtext(tag))
  builder.end(tag)

class StatusesIncludeImage(Filter):
  def filter(self, text):
    wanted_status = ['created_at', 'id', 'text', 'source', 'favorited']
    wanted_user = ['id', 'name', 'screen_name', 'profile_image_url', 'url']
    root = ET.fromstring(text)
    builder = ET.TreeBuilder()
    builder.start('statuses', {'type': 'array'})
    for status in root.findall('status'):
      builder.start('status', {})
      for tag in wanted_status:
        copy_element(builder, status, tag)

      user = status.find('user')
      builder.start('user', {})
      for tag in wanted_user:
        copy_element(builder, user, tag)
      builder.end('user')

      builder.end('status')
    builder.end('statuses')
    return ET.tostring(builder.close())

class StatusesTextOnly(Filter):
  def filter(self, text):
    wanted_status = ['created_at', 'id', 'text', 'source', 'favorited']
    wanted_user = ['id', 'name', 'screen_name', 'url']
    root = ET.fromstring(text)
    builder = ET.TreeBuilder()
    builder.start('statuses', {'type': 'array'})
    for status in root.findall('status'):
      builder.start('status', {})
      for tag in wanted_status:
        copy_element(builder, status, tag)

      user = status.find('user')
      builder.start('user', {})
      for tag in wanted_user:
        copy_element(builder, user, tag)
      builder.end('user')

      builder.end('status')
    builder.end('statuses')
    return ET.tostring(builder.close(), 'UTF-8')

class SingleStatusesIncludeImage(Filter):
  def filter(self, text):
    wanted_status = ['created_at', 'id', 'text', 'source', 'favorited']
    wanted_user = ['id', 'name', 'screen_name', 'profile_image_url', 'url']
    root = ET.fromstring(text)
    status = root.find('status')
    builder.start('status', {})
    for tag in wanted_status:
        copy_element(builder, status, tag)

    user = status.find('user')
    builder.start('user', {})
    for tag in wanted_user:
      copy_element(builder, user, tag)
    builder.end('user')

    builder.end('status')
    return ET.tostring(builder.close())

class SingleStatusesTextOnly(Filter):
  def filter(self, text):
    wanted_status = ['created_at', 'id', 'text', 'source', 'favorited']
    wanted_user = ['id', 'name', 'screen_name', 'url']
    root = ET.fromstring(text)
    status = root.find('status')
    logging.info(status)
    builder.start('status', {})
    for tag in wanted_status:
        copy_element(builder, status, tag)

    user = status.find('user')
    builder.start('user', {})
    for tag in wanted_user:
      copy_element(builder, user, tag)
    builder.end('user')
    builder.end('status')
    return ET.tostring(builder.close(), 'UTF-8')

class DirectMessageIncludeImage(Filter):
  def filter(self, text):
    wanted_dm = ['created_at', 'id', 'text', 'source', 'sender_id', 'recipient_id', 'sender_screen_name', 'recipient_screen_name']
    root = ET.fromstring(text)
    builder = ET.TreeBuilder()
    builder.start('direct-messages', {'type': 'array'})
    for status in root.findall('direct_message'):
      builder.start('direct_message', {})
      for tag in wanted_status:
        copy_element(builder, status, tag)

      sender = status.find('sender')
      builder.start('sender', {})
      copy_element(builder, sender, 'profile_image_url')
      builder.end('sender')

      recipient = status.find('recipient')
      builder.start('recipient', {})
      copy_element(builder, recipient, 'profile_image_url')
      builder.end('recipient')

      builder.end('direct_message')
    builder.end('direct-messages')
    return ET.tostring(builder.close())

class DirectMessageTextOnly(Filter):
  def filter(self, text):
    wanted_dm = ['created_at', 'id', 'text', 'source', 'sender_id', 'recipient_id', 'sender_screen_name', 'recipient_screen_name']
    root = ET.fromstring(text)
    builder = ET.TreeBuilder()
    builder.start('direct-messages', {'type': 'array'})
    for dm in root.findall('direct_message'):
      builder.start('direct_message', {})
      for tag in wanted_dm:
        copy_element(builder, dm, tag)
      builder.end('direct_message')
    builder.end('direct-messages')
    return ET.tostring(builder.close())

class SingleDirectMessageIncludeImage(Filter):
  def filter(self, text):
    wanted_dm = ['created_at', 'id', 'text', 'source', 'sender_id', 'recipient_id', 'sender_screen_name', 'recipient_screen_name']
    root = ET.fromstring(text)
    dm = root.find('direct_message')
    builder = ET.TreeBuilder()
    builder.start('direct_message', {})
    for tag in wanted_dm:
      copy_element(builder, dm, tag)

    sender = status.find('sender')
    builder.start('sender', {})
    copy_element(builder, sender, 'profile_image_url')
    builder.end('sender')

    recipient = status.find('recipient')
    builder.start('recipient', {})
    copy_element(builder, recipient, 'profile_image_url')
    builder.end('recipient')

    builder.end('direct_message')
    return ET.tostring(builder.close())


class SingleDirectMessageTextOnly(Filter):
  def filter(self, text):
    wanted_dm = ['created_at', 'id', 'text', 'source', 'sender_id', 'recipient_id', 'sender_screen_name', 'recipient_screen_name']
    root = ET.fromstring(text)
    dm = root.find('direct_message')
    builder = ET.TreeBuilder()
    builder.start('direct_message', {})
    for tag in wanted_dm:
      copy_element(builder, dm, tag)
    builder.end('direct_message')
    return ET.tostring(builder.close())
