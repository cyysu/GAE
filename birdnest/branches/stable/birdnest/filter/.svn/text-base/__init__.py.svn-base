import re
import logging
from urllib import quote

import simplejson
from birdnest.glm import get_location_by_cell, get_location_by_geo

c2l_cre = re.compile(r'c2l(%3A|:)(\d+)(%2C|,)(\d+)', re.I)
c2g_cre = re.compile(r'c2g(%3A|:)(\d+)(%2C|,)(\d+)', re.I)
l2g_cre = re.compile(r'l2g(%3A|:)(\d+\.\d+)(%2C|,)(\d+\.\d+)', re.I)

class Filter(object):
  def filter(self, text):
    return text

  def error_reason(self, text, reason):
    return reason

  def error_filter(self, text):
    return text

  def update_filter(self, text):
    m = c2l_cre.search(text)
    if m:
      try:
        lat, lon = get_location_by_cell(int(m.group(2)), int(m.group(4)))
        l = 'l:%0.6f,%0.6f ' % (lat, lon)
        l += 'http://maps.google.com/maps?q=%0.6f,%0.6f' % (lat, lon)
        text = c2l_cre.sub(quote(l), text)
      except Exception, why:
        logging.error(str(why))
    m = l2g_cre.search(text)
    if m:
      try:
        res = simplejson.loads(get_location_by_geo(m.group(2), m.group(4)))
        g = res['Placemark'][0]['address']
        text = l2g_cre.sub(quote(g), text)
      except Exception, why:
        logging.error(str(why))
    m = c2g_cre.search(text)
    if m:
      try:
        lat, lon = get_location_by_cell(int(m.group(2)), int(m.group(4)))
        res = simplejson.loads(get_location_by_geo(lat, lon))
        g = res['Placemark'][0]['address']
        text = c2g_cre.sub(quote(g), text)
      except Exception, why:
        logging.error(str(why))
    return text

def remove_html(text):
  return re.sub(r'<.*?>', '', text)
