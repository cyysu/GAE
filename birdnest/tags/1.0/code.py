#!/usr/bin/python2.5
import logging
import logging.handlers
import traceback
import web
import sys
import httplib
import urllib
from birdnest import filter
from birdnest.filter import json
from birdnest.filter import XML

logpath = 'log.txt'
twitterAPI = "http://twitter.com/"
rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s : %(pathname)s (%(lineno)d) --- %(message)s', 
                                              datefmt='%d %b %Y %H:%M:%S')
fileHandler = logging.handlers.TimedRotatingFileHandler(logpath, 'D', 1)
fileHandler.setFormatter(formatter)
rootLogger.addHandler(fileHandler)


class BaseProxy(object):

  required_header = ['Authorization',
                     'User-Agent',
                     'X-Twitter-Client',
                     'X-Twitter-Client-URL',
                     'X-Twitter-Client-Version']

  def __init__(self):
    data = ''
    fd = web.ctx.env['wsgi.input']
    while 1:
      chunked = fd.read(10000)
      if not chunked:
        break
      data += chunked
    web.ctx.data = data

  def _get_headers(self):
    headers = {}

    for header in self.required_header:
      # need caching or memoize trick to remember mapped key
      header_key = 'HTTP_' + header.replace('-','_').upper()
      if web.ctx.environ.has_key(header_key):
        headers[header] = web.ctx.environ[header_key]
    return headers

  def sendoutput(self, result):
    content = result.read()
    if result.status == 200:
      web.ctx.headers = result.getheaders()
      if len(content.strip()) > 0:
        filtered = self.filter(content)
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
        logging.error("%s \n\n %s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logging.error("%s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data()))
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
        logging.error("%s \n\n %s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logging.error("%s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data()))
      web.internalerror()

class OptimizedProxy(BaseProxy):
  user_agent = None

  def __init__(self):
    BaseProxy.__init__(self)

  def _get_headers(self):
    headers = BaseProxy._get_headers(self)
    headers['User-Agent'] = 'curl/7.18.0 (i486-pc-linux-gnu) libcurl/7.18.0 OpenSSL/0.9.8g zlib/1.2.3.3 libidn/1.1'
    if 'Authorization' not in headers:
      qs = web.input(__token__=None)
      if qs['__token__'] is not None:
        headers['Authorization'] = 'Basic '+qs['__token__']
        del qs['__token__']
        web.ctx.environ['QUERY_STRING'] = urllib.urlencode(qs)
    logging.debug(str(headers))
    return headers

  def sendoutput(self, result):
    content = result.read()
    if result.status == 200:
      web.ctx.headers = result.getheaders()
      if len(content.strip()) > 0:
        try:
          filtered = self.filter(content)
        except Exception, why:
          logging.debug(str(why))
          filtered = content
        web.header('content-length', len(filtered))
        web.webapi.output(filtered)
    elif result.status == 304:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      web.header('content-length', len(content))
      web.webapi.output(content)
    elif result.status == 400:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = self.error_filter(content)
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    elif result.status == 401 or result.status == 403:
      logging.debug(result.getheaders())
      logging.debug(web.ctx.environ)
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    elif result.status == 500:
      logging.debug(result.getheaders())
      logging.debug(web.ctx.environ)
      logging.debug(content)
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)
    else:
      web.ctx.headers = result.getheaders()
      web.ctx.status = str(result.status)+' '+result.reason
      filtered = ''
      web.header('content-length', len(filtered))
      web.webapi.output(filtered)


class JSONTwitPicProxy(BaseProxy, filter.Filter):

  required_header = ['Authorization',
                     'User-Agent',
                     'X-Twitter-Client',
                     'X-Twitter-Client-URL',
                     'X-Twitter-Client-Version']

  def __init__(self):
    BaseProxy.__init__(self)

  def _get_headers(self):
    headers = BaseProxy._get_headers(self)
    headers['Content-Type'] = web.ctx.environ['CONTENT_TYPE']
    return headers

  def parse_response(self, response):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(response)
    return root

  def sendoutput(self, result):
    import simplejson
    content = result.read()
    logging.debug(content)
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

  def POST(self, params):
    result = None
    target_url = '/' +params 
    headers = self._get_headers()
    httpcon = httplib.HTTPConnection('twitpic.com', 80)
    logging.debug(str(headers))
    #logging.debug(web.data())
    try:
      httpcon.request('POST', target_url, headers=headers, body=web.data())
      twitter_response = httpcon.getresponse()
      self.sendoutput(twitter_response)
    except Exception, inst:
      if result:
        logging.error("%s \n\n %s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data(), twitter_response.read()))
      else:
        logging.error("%s \n\n %s \n\n %s \n\n %s" % (target_url, str(inst), headers, web.data()))
      web.internalerror()


    
class NoFilterProxy(BaseProxy, filter.Filter):
  pass

class NoFilterOptimizedProxy(OptimizedProxy, filter.Filter):
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
    '/text/(statuses/update\.json.*)', 'JSONSingleStatusesTextOnlyProxy',
    '/text/(statuses/update\.xml.*)', 'XMLSingleStatusesTextOnlyProxy',
    '/text/(direct_messages\.json.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages\.xml.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages/sent\.json.*)', 'JSONDirectMessageTextOnlyProxy',
    '/text/(direct_messages/sent\.xml.*)', 'XMLDirectMessageTextOnlyProxy',
    '/text/(direct_messages/new\.json.*)', 'JSONSingleDirectMessageTextOnlyProxy',
    '/text/(direct_messages/new\.xml.*)', 'XMLSingleDirectMessageTextOnlyProxy',
    '/text/(direct_messages/delete/\d+\.json.*)', 'JSONSingleDirectMessageTextOnlyProxy',
    '/text/twitpic/(api/uploadAndPost.*)', 'JSONTwitPicProxy',

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

    '/(.*)', 'BaseProxy',
    )

def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.cgi as flups
    return flups.WSGIServer(func).run()
web.wsgi.runfcgi = runfcgi

#web.webapi.internalerror = web.debugerror
if __name__ == "__main__": web.run(urls, globals(), web.reloader)
