
# -*- coding: utf-8 -*-
from oauth2client.client import OAuth2WebServerFlow

from jinja2 import Environment, PackageLoader

from uuid import uuid4
from urllib import urlencode
import os
import urllib
import httplib
import webapp2
import jinja2
import json


from google.appengine.api import users
from google.appengine.api import urlfetch



CLIENT_ID = "756955635303-56djtcthh7bngf9ba89dvuvjja4o10m9.apps.googleusercontent.com"
CLIENT_SECRET = "ZjkWIQ6qsQIqs0SVavGwYhOn" 

#REDIRECT_URI = "http://oauth2implementation-166604.appspot.com/oauth2callback"
#HOME_URL ="http://oauth2implementation-166604.appspot.com"

REDIRECT_URI = "http://localhost:8080/oauth2callback"
HOME_URL ="http://localhost:8080/"

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)




state_val = str(uuid4())

class Oauth2callback(webapp2.RequestHandler):
	def get(self):
		
		callback_state = self.request.get('state')
		code = self.request.get('code')

		if callback_state != state_val:
			template_values = {
				'home_url':HOME_URL
			}
			template = JINJA_ENVIRONMENT.get_template('state_error.html')
			self.response.write(template.render(template_values))
			return
		header = {
			'Content-Type':'application/x-www-form-urlencoded'
		}
		data_to_post ={
			'code':code,
			'client_id':CLIENT_ID,
			'client_secret':CLIENT_SECRET,
			'redirect_uri':REDIRECT_URI,
			'grant_type':'authorization_code'
		}
		encoded_data = urllib.urlencode(data_to_post)
		result = urlfetch.fetch("https://www.googleapis.com/oauth2/v4/token/",headers=header,payload=encoded_data,method=urlfetch.POST)
		token = json.loads(result.content)

		#self.response.write(token)
		try:
			auth = 'Bearer ' + token['access_token']

			header = {
				'Authorization': auth
			}
		except:
			template_values = {
				'home_url':HOME_URL
			}
			template = JINJA_ENVIRONMENT.get_template('server_error.html')
			self.response.write(template.render(template_values))
			return

		response = urlfetch.fetch(url="https://www.googleapis.com/plus/v1/people/me",headers=header,method=urlfetch.GET)

		token_use = json.loads(response.content)

		#self.response.write(token_use)
		
		token_email = token_use['emails']
		token_name = token_use['name']
		template_values = {
			'email':token_email[0]['value'],
			#'gurl':token_use['url'],
			'firstName':token_name['givenName'],
			'lastName':token_name['familyName'],
			'state':callback_state,
			'home_url':HOME_URL
		}


		template = JINJA_ENVIRONMENT.get_template('oauthcallback.html')
		self.response.write(template.render(template_values))


class MainPage(webapp2.RequestHandler):
	def get(self):
		flow = OAuth2WebServerFlow(client_id=CLIENT_ID,client_secret=CLIENT_SECRET,scope="email",redirect_uri=REDIRECT_URI)

		auth_uri = flow.step1_get_authorize_url()
		
		template_values = {
			'url': auth_uri + "&state=" + state_val
		}
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/oauth2callback', Oauth2callback),
], debug=True)
