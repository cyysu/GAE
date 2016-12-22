# -*- coding: utf-8 -*-
# Copyright under  the latest Apache License 2.0

import wsgiref.handlers, urlparse, base64, logging
from cgi import parse_qsl
from google.appengine.ext import webapp
from google.appengine.api import urlfetch, urlfetch_errors
from wsgiref.util import is_hop_by_hop
from uuid import uuid4
import oauth

gtap_version = '0.4.2'

CONSUMER_KEY = ''
CONSUMER_SECRET = ''

USER_PASSWORD = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET=''

gtap_message = """
    <html>
        <head>
        <title>GAE Twitter API Proxy</title>
        <link href='https://appengine.google.com/favicon.ico' rel='shortcut icon' type='image/x-icon' />
        <style>body { padding: 20px 40px; font-family: Verdana, Helvetica, Sans-Serif; font-size: medium; }</style>
        </head>
        <body><h2>GTAP v#gtap_version# is running!</h2></p>
        <p>This is a simple solution on Google App Engine which can proxy the HTTP request to twitter's official REST API url.</p>
        <p><font color='red'><b>Don't forget the \"/\" at the end of your api proxy address!!!.</b></font></p>
    </body></html>
    """

def success_output(handler, content, content_type='text/html'):
    handler.response.set_status(200)
    handler.response.headers.add_header('GTAP-Version', gtap_version)
    handler.response.headers.add_header('Content-Type', content_type)
    handler.response.out.write(content)

def error_output(handler, content, content_type='text/html', status=503):
    handler.response.set_status(status)
    handler.response.headers.add_header('GTAP-Version', gtap_version)
    handler.response.headers.add_header('Content-Type', content_type)
    handler.response.out.write("Gtap Server Error:<br />")
    return handler.response.out.write(content)


class MainPage(webapp.RequestHandler):

    def conver_url(self, orig_url):
        (scm, netloc, path, params, query, _) = urlparse.urlparse(orig_url)
        
        path_parts = path.split('/')
        
        if path_parts[1] == 'api' or path_parts[1] == 'search':
            sub_head = path_parts[1]
            path_parts = path_parts[2:]
            path_parts.insert(0,'')
            new_path = '/'.join(path_parts).replace('//','/')
            new_netloc = sub_head + '.twitter.com'
        elif path_parts[1].startswith('search'):
            new_path = path
            new_netloc = 'search.twitter.com'
        else:
            new_path = path
            new_netloc = 'twitter.com'
    
        new_url = urlparse.urlunparse(('https', new_netloc, new_path.replace('//','/'), params, query, ''))
        return new_url, new_path

    def parse_auth_header(self, headers):
        username = None
        password = None
        
        if 'Authorization' in headers :
            auth_header = headers['Authorization']
            auth_parts = auth_header.split(' ')
            user_pass_parts = base64.b64decode(auth_parts[1]).split(':')
            username = user_pass_parts[0]
            password = user_pass_parts[1]
    
        return username, password

    def do_proxy(self, method):
        orig_url = self.request.url
        orig_body = self.request.body

        new_url,new_path = self.conver_url(orig_url)

        if new_path == '/' or new_path == '':
            global gtap_message
            gtap_message = gtap_message.replace('#gtap_version#', gtap_version)
            return success_output(self, gtap_message )
        
        username, password = self.parse_auth_header(self.request.headers)
        if password!=USER_PASSWORD :
            return error_output(self, 'Wrong password.')

        user_access_token = None
        
        callback_url = "%s/oauth/verify" % self.request.host_url
        client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, callback_url)

        if username is None :
            protected=False
            user_access_token, user_access_secret = '', ''
        else:
            protected=True
            user_access_token, user_access_secret  = ACCESS_TOKEN, ACCESS_TOKEN_SECRET
        
        additional_params = dict([(k,v) for k,v in parse_qsl(orig_body)])

        use_method = urlfetch.GET if method=='GET' else urlfetch.POST

        try :
            data = client.make_request(url=new_url, token=user_access_token, secret=user_access_secret, 
                                   method=use_method, protected=protected, 
                                   additional_params = additional_params)
        except Exception,error_message:
            logging.debug( error_message )
            error_output(self, content=error_message)
        else :
            #logging.debug(data.headers)
            self.response.headers.add_header('GTAP-Version', gtap_version)
            for res_name, res_value in data.headers.items():
                if is_hop_by_hop(res_name) is False and res_name!='status':
                    self.response.headers.add_header(res_name, res_value)
            self.response.out.write(data.content)

    def post(self):
        self.do_proxy('POST')
    
    def get(self):
        self.do_proxy('GET')


def main():
    application = webapp.WSGIApplication( [
        (r'/.*',         MainPage)
        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
    
if __name__ == "__main__":
  main()
