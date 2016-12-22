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

CONSUMER_KEY = 'lhH8Iz1L9xSEToeafrQ2nFYE2'
CONSUMER_SECRET = 'eLQnmOtHjFHBQFQAN8V27uZsLtSjeBpcf456I88bBB1645LPII'

gtap_message = """
    <html>
        <head>
        <title>GAE Twitter API Proxy</title>
        <link href='https://appengine.google.com/favicon.ico' rel='shortcut icon' type='image/x-icon' />
        <style>body { padding: 20px 40px; font-family: Verdana, Helvetica, Sans-Serif; font-size: medium; }</style>
        </head>
        <body><h2>GTAP v#gtap_version# is running!</h2></p>
        <p><a href='/oauth/session'><img src='/static/sign-in-with-twitter.png' border='0'></a> <== Need Fuck GFW First!!
        or <a href='/oauth/change'>change your key here</a></p>
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
        user_access_token = None

        callback_url = "%s/oauth/verify" % self.request.host_url
        client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, callback_url)

        if username is None :
            protected=False
            user_access_token, user_access_secret = '', ''
        else:
            protected=True
            user_access_token, user_access_secret  = client.get_access_from_db(username, password)
            if user_access_token is None :
                return error_output(self, 'Can not find this user from db')

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


class OauthPage(webapp.RequestHandler):

    def get(self, mode=""):
        callback_url = "%s/oauth/verify" % self.request.host_url
        client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, callback_url)

        if mode=='session':
            # step C Consumer Direct User to Service Provider
            try:
                url = client.get_authorization_url()
                self.redirect(url)
            except Exception,error_message:
                self.response.out.write( error_message )


        if mode=='verify':
            # step D Service Provider Directs User to Consumer
            auth_token = self.request.get("oauth_token")
            auth_verifier = self.request.get("oauth_verifier")

            # step E Consumer Request Access Token
            # step F Service Provider Grants Access Token
            try:
                access_token, access_secret, screen_name = client.get_access_token(auth_token, auth_verifier)
                self_key = '%s' % uuid4()
                # Save the auth token and secret in our database.
                client.save_user_info_into_db(username=screen_name, password=self_key,
                                              token=access_token, secret=access_secret)
                show_key_url = '%s/oauth/showkey?name=%s&key=%s' % (
                                                                       self.request.host_url,
                                                                       screen_name, self_key)
                self.redirect(show_key_url)
            except Exception,error_message:
                logging.debug("oauth_token:" + auth_token)
                logging.debug("oauth_verifier:" + auth_verifier)
                logging.debug( error_message )
                self.response.out.write( error_message )

        if mode=='showkey':
            screen_name = self.request.get("name")
            self_key = self.request.get("key")
            out_message = """
                <html><head><title>GTAP</title>
                <style>body { padding: 20px 40px; font-family: Courier New; font-size: medium; }</style>
                </head><body><p>
                your twitter's screen name : <b>#screen_name#</b> <br /><br />
                the Key of this API : <b>#self_key#</b> <a href="#api_host#/oauth/change?name=#screen_name#&key=#self_key#">you can change it now</a><br /><br />
                </p>
                <p>
                In the third-party client of Twitter which support Custom API address,<br />
                set the API address as <b>#api_host#/</b> or <b>#api_host#/api/1/</b> , <br />
                and set Search API address as <b>#api_host#/search/</b> . <br />
                Then you must use the <b>Key</b> as your password when Sign-In in these clients.
                </p></body></html>
                """
            out_message = out_message.replace('#api_host#', self.request.host_url)
            out_message = out_message.replace('#screen_name#', screen_name)
            out_message = out_message.replace('#self_key#', self_key)
            self.response.out.write( out_message )

        if mode=='change':
            screen_name = self.request.get("name")
            self_key = self.request.get("key")
            out_message = """
                <html><head><title>GTAP</title>
                <style>body { padding: 20px 40px; font-family: Courier New; font-size: medium; }</style>
                </head><body><p><form method="post" action="%s/oauth/changekey">
                your screen name of Twitter : <input type="text" name="name" size="20" value="%s"> <br /><br />
                your old key of this API : <input type="text" name="old_key" size="50" value="%s"> <br /><br />
                define your new key of this API : <input type="text" name="new_key" size="50" value=""> <br /><br />
                <input type="submit" name="_submit" value="Change the Key">
                </form></p></body></html>
                """ % (self.request.host_url, screen_name, self_key)
            self.response.out.write( out_message )


    def post(self, mode=''):

        callback_url = "%s/oauth/verify" % self.request.host_url
        client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, callback_url)

        if mode=='changekey':
            screen_name = self.request.get("name")
            old_key = self.request.get("old_key")
            new_key = self.request.get("new_key")
            user_access_token, user_access_secret  = client.get_access_from_db(screen_name, old_key)

            if user_access_token is None or user_access_secret is None:
                logging.debug("screen_name:" + screen_name)
                logging.debug("old_key:" + old_key)
                logging.debug("new_key:" + new_key)
                self.response.out.write( 'Can not find user from db, or invalid old_key.' )
            else:
                try:
                    client.save_user_info_into_db(username=screen_name, password=new_key,
                                                  token=user_access_token, secret=user_access_secret)
                    show_key_url = '%s/oauth/showkey?name=%s&key=%s' % (
                                                                        self.request.host_url,
                                                                        screen_name, new_key)
                    self.redirect(show_key_url)
                except Exception,error_message:
                    logging.debug("screen_name:" + screen_name)
                    logging.debug("old_key:" + old_key)
                    logging.debug("new_key:" + new_key)
                    logging.debug( error_message )
                    self.response.out.write( error_message )

        if mode=='access_token':
            # TwitBird needs this to
            error_output(self, 'Oops!')


def main():
    application = webapp.WSGIApplication( [
        (r'/oauth/(.*)', OauthPage),
        (r'/.*',         MainPage)
        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
