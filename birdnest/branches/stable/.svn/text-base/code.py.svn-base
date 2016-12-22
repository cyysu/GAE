#!/usr/bin/python2.5
import logging
import logging.handlers
import sys
import traceback
import web
import httplib
import urllib
from birdnest.filter import Filter
from birdnest.filter import json
from birdnest.filter import XML

twitterAPI = "http://twitter.com/"
logger = logging.getLogger()
ua_logger = logging.getLogger('useragent')

picture_gateways = {
  'twitpic': ('twitpic.com', 80, '/'),
  'twitgoo': ('twitgoo.com', 80, '/'),
  'upicme': ('upic.me', 80, '/'),
  'yfrog' : ('yfrog.com', 80, '/'),
}


class BaseProxy(object):

  required_header = ['Authorization',
                     'User-Agent',
                     'X-Twitter-Client',
                     'X-Twitter-Client-URL',
                     'X-Twitter-Client-Version']

  unwanted_header = []

  def __init__(self):
    if web.ctx.env['REQUEST_METHOD'] == 'POST':
      data = ''
      fd = web.ctx.env['wsgi.input']
      if web.ctx.env['SERVER_NAME'] == 'localhost':
        length = int(web.ctx.env.get('CONTENT_LENGTH', 10000))
        data = fd.read(length)
      else:
        while 1:
          chunked = fd.read(10000)
          if not chunked:
            break
          data += chunked
      web.ctx.data = data
    ua_logger.info(web.ctx.environ.get('HTTP_USER_AGENT', 'None'))

  def _get_headers(self):
    headers = {}

    for header in self.required_header:
      # need caching or memoize trick to remember mapped key
      header_key = 'HTTP_' + header.replace('-','_').upper()
      if web.ctx.environ.has_key(header_key):
        headers[header] = web.ctx.environ[header_key]
    return headers

  def _filter_headers(self, headers):
    return filter(lambda i: i[0].lower() not in self.unwanted_header, headers)

  def sendoutput(self, result):
    content = result.read()
    if result.status == 200:
      web.ctx.headers = result.getheaders()
      if len(content.strip()) > 0:
        filtered = self.filter(content)
        web.ctx.headers = filter(lambda i: i[0].lower() != 'content-length', result.getheaders())
        logger.debug(str(web.ctx.headers))
        web.header('content-length', len(filtered))
        web.webapi.output(filtered)
    else:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      web.webapi.output(content)

  def GET(self, params):    
    result = None
    headers = self._get_headers()

    target_url = '/' +params 
    if web.ctx.environ.get('QUERY_STRING', None):
      target_url += '?'+web.ctx.environ['QUERY_STRING']
    httpcon = httplib.HTTPConnection('twitter.com', 80)
    try:
      httpcon.request('GET', target_url, headers=headers)
      twitter_response = httpcon.getresponse()
      self.sendoutput(twitter_response)
    except Exception, inst:
      if result:
        logger.error("%s\n\n%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logger.error("%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data()))
      web.internalerror()
      


  def POST(self, params):
    result = None
    target_url = '/' +params 
    headers = self._get_headers()
    httpcon = httplib.HTTPConnection('twitter.com', 80)
    try:
      httpcon.request('POST', target_url, headers=headers, body=web.data())
      twitter_response = httpcon.getresponse()
      self.sendoutput(twitter_response)
    except Exception, inst:
      if result:
        logger.error("%s\n\n%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logger.error("%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data()))
      web.internalerror()

class OptimizedProxy(BaseProxy):
  user_agent = None
  unwanted_header = ['status',
                     'x-runtime',
                     'etag',
                     'pragma',
                     'cache-control',
                     'content-length',
                     'set-cookie',
                     'vary',
                     'connection',
                     'x-transaction',
                     'x-revision',
                    ]

  def __init__(self):
    BaseProxy.__init__(self)

  def _get_headers(self):
    headers = BaseProxy._get_headers(self)
    if 'Authorization' not in headers:
      qs = web.input(__token__=None)
      if qs['__token__'] is not None:
        headers['Authorization'] = 'Basic '+qs['__token__']
        del qs['__token__']
        web.ctx.environ['QUERY_STRING'] = urllib.urlencode(qs)
    logger.debug(str(headers))
    headers['User-Agent'] = 'curl/7.18.0 (i486-pc-linux-gnu) libcurl/7.18.0 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.1'
    return headers

  def POST(self, params):
    if params.startswith('statuses/update.'):
      web.ctx.data = self.update_filter(web.data())
    return BaseProxy.POST(self, params)

  def sendoutput(self, result):
    content = result.read()
    if result.status == 200:
      web.ctx.headers = self._filter_headers(result.getheaders())
      if len(content.strip()) > 0:
        try:
          filtered = self.filter(content)
        except Exception, why:
          logger.error(str(why))
          filtered = content
        web.header('content-length', len(filtered))
        web.webapi.output(filtered)
    elif result.status == 304:
      web.ctx.headers = self._filter_headers(result.getheaders())
      web.ctx.status = str(result.status)+' '+result.reason
      web.header('content-length', len(content))
      web.webapi.output(content)
    elif result.status == 400:
      web.ctx.headers = self._filter_headers(result.getheaders())
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = self.error_filter(content)
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    elif result.status == 401 or result.status == 403:
      logger.debug(result.getheaders())
      logger.debug(web.ctx.environ)
      web.ctx.headers = self._filter_headers(result.getheaders())
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    elif result.status == 500:
      logger.debug(result.getheaders())
      logger.debug(web.ctx.environ)
      logger.debug(content)
      web.ctx.headers = self._filter_headers(result.getheaders())
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    else:
      web.ctx.headers = self._filter_headers(result.getheaders())
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)


class JSONTwitPicProxy(BaseProxy, Filter):

  required_header = ['Authorization',
                     'Content-Length',
                     'User-Agent',
                     'X-Twitter-Client',
                     'X-Twitter-Client-URL',
                     'X-Twitter-Client-Version']

  def __init__(self):
    BaseProxy.__init__(self)

  def _get_headers(self):
    headers = BaseProxy._get_headers(self)
    headers['Content-Type'] = web.ctx.environ['CONTENT_TYPE']
    logger.debug(str(headers))
    return headers

  def parse_response(self, response):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(response)
    return root

  def sendoutput(self, result):
    import simplejson
    content = result.read()
    logger.debug(content)
    if result.status == 200:
      web.ctx.headers = result.getheaders()
      if len(content.strip()) > 0:
        d = self.parse_response(content)
        err = d.find('err')
        if err is not None:
          reason = '%s %s' % (err.attrib['code'], err.attrib['msg'])
          response = {'error': reason}
          web.ctx.status = str(400)+' '+reason
        else:
          response = {'id': d.findtext('statusid')}
        content = simplejson.dumps(response)
        filtered = self.filter(content)
        web.header('content-length', len(filtered))
        web.webapi.output(filtered)
    else:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      web.webapi.output(content)

  def POST(self, gateway, params):
    result = None
    if gateway not in picture_gateways:
      gateway = 'twitpic'
    ghost, gport, gbaseurl = picture_gateways[gateway]
    target_url = '/' +params 
    headers = self._get_headers()
    httpcon = httplib.HTTPConnection(ghost, gport)
    #logger.debug(str(headers))
    #logger.debug(web.data())
    try:
      httpcon.request('POST', target_url, headers=headers, body=web.data())
      twitter_response = httpcon.getresponse()
      self.sendoutput(twitter_response)
    except Exception, inst:
      if result:
        logger.error("%s\n\n%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logger.error("%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, web.data()))
      web.internalerror()


class JSONTwitPicManualProxy(BaseProxy, Filter):

  required_header = ['Authorization',
                     'Content-Length',
                     'User-Agent',
                     'X-Twitter-Client',
                     'X-Twitter-Client-URL',
                     'X-Twitter-Client-Version']

  def __init__(self):
    BaseProxy.__init__(self)

  def _get_headers(self):
    headers = BaseProxy._get_headers(self)
    headers['Content-Type'] = web.ctx.environ['CONTENT_TYPE']
    logger.debug(str(headers))
    import re
    m = re.match(r'multipart/form-data;boundary=([^;]+); charset=UTF-8', headers['Content-Type'])
    if m:
        headers['Content-Type'] = 'multipart/form-data; charset=UTF-8; boundary=%s' % m.group(1)
        logger.debug('rewritten'+str(headers))
    return headers

  def parse_response(self, response):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(response)
    return root

  def sendoutput(self, result):
    import simplejson
    content = result.read()
    logger.debug(content)
    if result.status == 200:
      web.ctx.headers = result.getheaders()
      if len(content.strip()) > 0:
        d = self.parse_response(content)
        err = d.find('err')
        if err is not None:
          reason = '%s %s' % (err.attrib['code'], err.attrib['msg'])
          response = {'error': reason}
          web.ctx.status = str(400)+' '+reason
        else:
          from urllib import urlencode
          from cStringIO import StringIO
          import cgi
          import base64
          try:
            mediaurl = d.findtext('mediaurl')
            fp = StringIO(web.data())
            environ = {'REQUEST_METHOD': 'POST',
                       'CONTENT_TYPE': web.ctx.environ['CONTENT_TYPE'],
                       'CONTENT_LENGTH': len(web.data())}
            m = cgi.FieldStorage(fp, environ=environ)
            message = '%s %s' % (m['message'].value, mediaurl)
            qs = urlencode({'status': message, 'source': 'birdnest'})
            qs = self.update_filter(qs)
            headers = self._get_headers()
            headers['User-Agent'] = 'curl/7.18.0 (i486-pc-linux-gnu) libcurl/7.18.0 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.1'
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            headers['Authorization'] = 'Basic '+base64.encodestring(m['username'].value+':'+m['password'].value)[:-1]
            httpcon = httplib.HTTPConnection('twitter.com', 80)
            logger.debug(str(headers))
            logger.debug(qs)
            httpcon.request('POST', '/statuses/update.json', headers=headers, body=qs)
            twitter_response = httpcon.getresponse()
            content = twitter_response.read()
            #logger.debug(content)
            status = simplejson.loads(content)
            response = {'id': status['id']}
          except Exception, why:
            logger.error(str(why))
            response = {'error': str(why)}
            web.ctx.status = str(500)+' '+str(reason)
        content = simplejson.dumps(response)
        filtered = self.filter(content)
        web.header('content-length', len(filtered))
        web.webapi.output(filtered)
    else:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      web.webapi.output(content)

  def POST(self, gateway, params):
    result = None
    if gateway not in picture_gateways:
      gateway = 'twitpic'
    ghost, gport, gbaseurl = picture_gateways[gateway]
    target_url = '/'+params 
    headers = self._get_headers()
    httpcon = httplib.HTTPConnection(ghost, gport)
    #logger.debug(str(headers))
    #logger.debug(web.data())
    try:
      httpcon.request('POST', gbaseurl+'api/upload', headers=headers, body=web.data())
      twitter_response = httpcon.getresponse()
      self.sendoutput(twitter_response)
    except Exception, inst:
      if result:
        logger.error("%s\n\n%s\n\n%s\n\n%s" % (target_url, str(inst), headers, twitter_response.read()))
      else:
        logger.error("%s\n\n%s\n\n%s" % (target_url, str(inst), headers))
      web.internalerror()


class GoogleLocationMobile:
  def GET(self, cellid, lac):
    import simplejson
    from birdnest.glm import get_location_by_cell
    try:
      lat, long = get_location_by_cell(int(cellid), int(lac))
      response = {'status': 'OK',
                  'lat': lat,
                  'long': long}
    except Exception, why:
      response = {'status': 'ERR',
                  'message': str(why)}
    content = simplejson.dumps(response)
    web.header('content-length', len(content))
    web.webapi.output(content)
    

class GoogleReverseGeocoder:
  def GET(self, latitude, longitude):
    import simplejson
    from birdnest.glm import get_location_by_geo
    try:
      o = simplejson.loads(get_location_by_geo(latitude, longitude))
      response = {'status': 'OK',
                  'address': o['Placemark'][0]['address']}
    except Exception, why:
      response = {'status': 'ERR',
                  'message': str(why)}
    content = simplejson.dumps(response)
    web.header('content-length', len(content))
    web.webapi.output(content)
    



class NoFilterProxy(BaseProxy, Filter):
  pass

class NoFilterOptimizedProxy(OptimizedProxy, Filter):
  pass

class JSONStatusesIncludeImageProxy(OptimizedProxy, json.StatusesIncludeImage):
  pass

class JSONStatusesTextOnlyProxy(OptimizedProxy, json.StatusesTextOnly):
  pass

class JSONSingleStatusesIncludeImageProxy(OptimizedProxy, json.SingleStatusesIncludeImage):
  pass

class JSONSingleStatusesTextOnlyProxy(OptimizedProxy, json.SingleStatusesTextOnly):
  pass

class JSONDirectMessageTextOnlyProxy(OptimizedProxy, json.DirectMessageTextOnly):
  pass

class JSONDirectMessageIncludeImageProxy(OptimizedProxy, json.DirectMessageIncludeImage):
  pass

class JSONSingleDirectMessageTextOnlyProxy(OptimizedProxy, json.SingleDirectMessageTextOnly):
  pass

class JSONSingleDirectMessageIncludeImageProxy(OptimizedProxy, json.SingleDirectMessageIncludeImage):
  pass

class XMLStatusesIncludeImageProxy(OptimizedProxy, XML.StatusesIncludeImage):
  pass

class XMLStatusesTextOnlyProxy(OptimizedProxy, XML.StatusesTextOnly):
  pass

class XMLSingleStatusesIncludeImageProxy(OptimizedProxy, XML.SingleStatusesIncludeImage):
  pass

class XMLSingleStatusesTextOnlyProxy(OptimizedProxy, XML.SingleStatusesTextOnly):
  pass

class XMLDirectMessageTextOnlyProxy(OptimizedProxy, XML.DirectMessageTextOnly):
  pass

class XMLDirectMessageIncludeImageProxy(OptimizedProxy, XML.DirectMessageIncludeImage):
  pass

class XMLSingleDirectMessageTextOnlyProxy(OptimizedProxy, XML.SingleDirectMessageTextOnly):
  pass

class XMLSingleDirectMessageIncludeImageProxy(OptimizedProxy, XML.SingleDirectMessageIncludeImage):
  pass



urls  = (

    '/api/(.*)', 'NoFilterProxy',
    '/optimized/(.*)', 'NoFilterOptimizedProxy',

    '/text/(statuses/public_timeline\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/public_timeline\.xml.*)', 'XMLStatusesTextOnlyProxy',
    '/text/(statuses/user_timeline\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/user_timeline\.xml.*)', 'XMLStatusesTextOnlyProxy',
    '/text/(statuses/friends_timeline\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/friends_timeline\.xml.*)', 'XMLStatusesTextOnlyProxy',

    '/text/(statuses/friends_timeline/\w+\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/friends_timeline/\w+\.xml.*)', 'XMLStatusesTextOnlyProxy',

    '/text/(statuses/replies\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/replies\.xml.*)', 'XMLStatusesTextOnlyProxy',
    '/text/(statuses/mentions\.json.*)', 'JSONStatusesTextOnlyProxy',
    '/text/(statuses/mentions\.xml.*)', 'XMLStatusesTextOnlyProxy',
    '/text/(statuses/update\.json.*)', 'JSONSingleStatusesTextOnlyProxy',
    '/text/(statuses/update\.xml.*)', 'XMLSingleStatusesTextOnlyProxy',
    '/text/(direct_messages\.json.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages\.xml.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages/sent\.json.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages/sent\.xml.*)', 'XMLDirectMessageTextOnlyProxy',
    '/text/(direct_messages/new\.json.*)', 'JSONSingleDirectMessageTextOnlyProxy',
    '/text/(direct_messages/new\.xml.*)', 'XMLSingleDirectMessageTextOnlyProxy',
    '/text/(direct_messages/delete/\d+\.json.*)', 'JSONSingleDirectMessageTextOnlyProxy',
#    '/text/(upicme)/(api/uploadAndPost.*)', 'JSONTwitPicProxy',
    '/text/(\w+)/(api/uploadAndPost.*)', 'JSONTwitPicManualProxy',

    '/text/(.*)', 'NoFilterOptimizedProxy',

    '/image/(statuses/public_timeline\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/public_timeline\.xml.*)', 'XMLStatusesIncludeImageProxy',
    '/image/(statuses/user_timeline\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/user_timeline\.xml.*)', 'XMLStatusesIncludeImageProxy',
    '/image/(statuses/friends_timeline\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/friends_timeline\.xml.*)', 'XMLStatusesIncludeImageProxy',
    '/image/(statuses/friends_timeline/\w+\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/friends_timeline/\w+\.xml.*)', 'XMLStatusesIncludeImageProxy',

    '/image/(statuses/replies\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/replies\.xml.*)', 'XMLStatusesIncludeImageProxy',
    '/image/(statuses/mentions\.json.*)', 'JSONStatusesIncludeImageProxy',
    '/image/(statuses/mentions\.xml.*)', 'XMLStatusesIncludeImageProxy',
    '/image/(statuses/update\.json.*)', 'JSONSingleStatusesIncludeImageProxy',
    '/image/(statuses/update\.xml.*)', 'JSONSingleStatusesIncludeImageProxy',
    '/image/(direct_messages\.json.*)', 'JSONDirectMessageIncludeImageProxy',
    '/image/(direct_messages\.xml.*)', 'XMLDirectMessageIncludeImageProxy',
    '/image/(direct_messages/sent\.json.*)', 'JSONDirectMessageIncludeImageProxy',
    '/image/(direct_messages/sent\.xml.*)', 'XMLDirectMessageIncludeImageProxy',

    '/image/(direct_messages/new\.json.*)', 'JSONSingleDirectMessageIncludeImageProxy',
    '/image/(direct_messages/new\.xml.*)', 'XMLSingleDirectMessageIncludeImageProxy',

    '/image/(direct_messages/delete/\d+\.json.*)', 'JSONSingleDirectMessageIncludeImageProxy',
    '/image/(direct_messages/delete/\d+\.xml.*)', 'XMLSingleDirectMessageIncludeImageProxy',
    '/image/(.*)', 'NoFilterOptimizedProxy',

    '/glm/cell/(\d+)/(\d+)', 'GoogleLocationMobile',
    '/glm/rgeo/([0-9.]+)/([0-9.]+)', 'GoogleReverseGeocoder',

    '/(.*)', 'BaseProxy',
    )

def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.cgi as flups
    return flups.WSGIServer(func).run()
web.wsgi.runfcgi = runfcgi

#web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
    logpath = 'log.txt'
    logger.setLevel(logging.DEBUG)
    fh = logging.handlers.RotatingFileHandler(
             logpath, maxBytes=20*1024*1024, backupCount=5)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
                    fmt='%(asctime)s %(levelname)s %(pathname)s:%(lineno)d %(message)s',
                    datefmt='%Y%m%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logpath = 'useragent.txt'
    ua_logger.setLevel(logging.INFO)
    fh = logging.handlers.RotatingFileHandler(
             logpath, maxBytes=20*1024*1024, backupCount=5)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
                    fmt='%(asctime)s %(message)s',
                    datefmt='%Y%m%d %H:%M:%S')
    fh.setFormatter(formatter)
    ua_logger.addHandler(fh)

    web.run(urls, globals(), web.reloader)
