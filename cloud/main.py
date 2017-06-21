# -*- coding: utf-8 -*-
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import client
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
from google.appengine.ext import ndb

#OAUTH INFORMATION
CLIENT_ID = "918504728223-4b7pks0poocj2enltfu4nt6eciheq6dr.apps.googleusercontent.com"
CLIENT_SECRET = "PBTg2lkGSkl9oM4z7-B-TokD"

REDIRECT_URI = "http://yanda-final-project.appspot.com/callback"
HOME_URL = "http://yanda-final-project.appspot.com"

#REDIRECT_URI = "http://localhost:8080/callback"
#HOME_URL = "http://localhost:8080/"


#RENDERING ENGINE
JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)



class StateVar:
	state_value = ""

class Student(ndb.Model):
	id = ndb.StringProperty()
	name = ndb.StringProperty(required=True)
	cohort = ndb.StringProperty()
	grad_year = ndb.IntegerProperty()
	enrolled = ndb.BooleanProperty()
	s_token_id = ndb.StringProperty()

class Textbook(ndb.Model):
	id = ndb.StringProperty()
	title = ndb.StringProperty(required=True)
	edition = ndb.IntegerProperty()
	page_count = ndb.IntegerProperty()
	student_borrower = ndb.StringProperty()
	t_token_id = ndb.StringProperty()



class Callback(webapp2.RequestHandler):
	def get(self):
		callback_state = self.request.get('state')
		code = self.request.get('code')
		
		# error with state variable
		# state_error webpage will redirect home
		if callback_state != StateVar.state_value:
			template_values = {
				'home_url':HOME_URL
			}
			template = JINJA_ENVIRONMENT.get_template('state_error.html')
			self.response.write(template.render(template_values))
			return
		StateVar.state_value = ""
		
		

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

		fetch_token = token['id_token']
		
		currentToken = client.verify_id_token(fetch_token,None)
		userIdToken = currentToken['sub']

		template_values = {
			'home_url': HOME_URL,
			'token_info': userIdToken
		}

		template = JINJA_ENVIRONMENT.get_template('callback.html')
		self.response.write(template.render(template_values))

class StudentHandler(webapp2.RequestHandler):
	#READ
	def get(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']			
			#self.response.write(userId)
		else:
			#forbidden access
			self.response.set_status(403)
			return

		#get an individual student	
		if id:
			student = ndb.Key(urlsafe=id).get()
			#make sure that the student has the correct s_token_id
			if student.s_token_id == userId:
				if student:
					student_dict = student.to_dict()
					student_dict['self'] = '/students/' +id
					self.response.write(json.dumps(student_dict))
					self.response.headers['Content-Type'] = 'application/json'
				else:
					self.response.write("id invalid")
					self.response.set_status(400)
					return	
			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
				return

		#get all students in the database that belong to this s_token_id
		else:
			all_students = Student.query(Student.s_token_id == userId).fetch()
			list_students = []
			for student in all_students:
				student_dict = student.to_dict()
				list_students.append(student_dict)
			self.response.write(json.dumps(list_students))
			self.response.headers['Content-Type'] = 'application/json'

	#ADD
	def post(self):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']
		else:
			#forbidden access
			self.response.set_status(403)
			return

		student_data = json.loads(self.request.body)
		if 'name' in student_data:
			new_student = Student(name=student_data['name'],s_token_id=userId)
			if 'cohort' in student_data:
				new_student.cohort = student_data['cohort']
			else: 
				new_student.cohort = None
			if 'grad_year' in student_data:
				new_student.grad_year = student_data['grad_year']
			else: 
				new_student.grad_year = None
			if 'enrolled' in student_data:
				new_student.enrolled = student_data['enrolled']
			else: 
				new_student.enrolled = None
			new_student.put()
			new_student.id = new_student.key.urlsafe()
			new_student.put()

			student_dict = new_student.to_dict()
			student_dict['self'] = "/students/" + new_student.id
			self.response.write(json.dumps(student_dict))
			self.response.headers['Content-Type'] = 'application/json'
			self.response.set_status(200)
													
		else:
			#bad request - name required
			self.response.set_status(400)

	#DELETE
	def delete(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']			
			#self.response.write(userId)
		else:
			#forbidden access
			self.response.set_status(403)
			return
		
		if id:
			if id == "all":
				all_students = Student.query(Student.s_token_id == userId).fetch()
				list_students = []
				for student in all_students:
					student.key.delete()

				self.response.write("all students for "+userId+" has been deleted")
				self.response.set_status(200)
			
			else:
				student_key = ndb.Key(urlsafe=id)
				student = student_key.get()
				if student is not None:
					if student.s_token_id == userId:
						student.key.delete()
						self.response.write("delete successful")
						self.response.set_status(200)
					else:
						#forbidden access
						self.response.write("this id is not associated with your account")
						self.response.set_status(403)
				else:
					self.response.write("this id does not exist")
					self.response.set_status(404)

		else:
			self.response.write("id error")
			self.response.set_status(400)

	#REPLACE
	def put(self,id=None):
		
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']
		else:
			self.response.set_status(403)
			return


		if id:
			student_data = json.loads(self.request.body)
			student_key = ndb.Key(urlsafe=id)
			student = student_key.get()

			
			#make sure that the student belongs to this s_token_id
			if student.s_token_id == userId:
				if 'name' in student_data:
					student.name = student_data['name']

					if 'cohort' in student_data:
						student.cohort = student_data['cohort']
					else:
						student.cohort = None

					if 'grad_year' in student_data:
						student.grad_year = student_data['grad_year']
					else:
						student.grad_year = None

					if 'enrolled' in student_data:
						student.enrolled = student_data['enrolled']
					else:
						student.enrolled = None

					student.put()
					self.response.set_status(200)
					self.response.write("put successful")

				else:
					self.response.write("name is required")
					self.response.set_status(400)

			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
			
		else:
			self.response.write("id is required")
			self.response.set_status(400)


	#UPDATE
	def patch(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']			
			#self.response.write(userId)
		else:
			#forbidden access
			self.response.set_status(403)
			return


		if id:
			student_data = json.loads(self.request.body)
			student_key = ndb.Key(urlsafe=id)
			student = student_key.get()
			#make sure that the student belongs to this s_token_id
			if student.s_token_id == userId:
				if 'name' in student_data:
					student.name = student_data['name']

					if 'cohort' in student_data:
						student.cohort = student_data['cohort']
					if 'grad_year' in student_data:
						student.grad_year = student_data['grad_year']
					if 'enrolled' in student_data:
						student.enrolled = student_data['enrolled']
					
					student.put()
					self.response.set_status(200)
					self.response.write("patch successful")

				else:
					self.response.write("name is required")
					self.response.set_status(400)

			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
		else:
			self.response.write("id is required")
			self.response.set_status(400)
		
class TextbookHandler(webapp2.RequestHandler):
	#READ
	def get(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']			
			#self.response.write(userId)
		else:
			#forbidden access
			self.response.set_status(403)
			return

		if id:
			textbook = ndb.Key(urlsafe=id).get()
			#make sure that the textbook has the correct t_token_id

			if textbook.t_token_id == userId:
				if textbook:
					textbook_dict = textbook.to_dict()
					textbook_dict['self'] = '/textbooks/' + id
					self.response.write(json.dumps(textbook_dict))
					self.response.headers['Content-Type'] = 'application/json'
				else:
					self.response.write("id invalid")
					self.response.set_status(400)
					return				
			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
				return


		else:
			all_textbooks = Textbook.query(Textbook.t_token_id == userId).fetch()
			list_textbooks = []
			for textbook in all_textbooks:
				textbook_dict = textbook.to_dict()
				list_textbooks.append(textbook_dict)
			self.response.write(json.dumps(list_textbooks))
			self.response.headers['Content-Type'] = 'application/json'

	#ADD
	def post(self):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']
		else:
			#forbidden access
			self.response.set_status(403)
			return

		textbook_data = json.loads(self.request.body)
		if 'title' in textbook_data:
			new_textbook = Textbook(title=textbook_data['title'],t_token_id=userId)
			if 'edition' in textbook_data:
				new_textbook.edition = textbook_data['edition']
			else:
				new_textbook.edition = None
			if 'page_count' in textbook_data:
				new_textbook.page_count = textbook_data['page_count']
			if 'student_borrower' in textbook_data:
				#find the student in the entire Student list for this userId
				student_check = Student.query(ndb.AND(Student.s_token_id == userId,Student.id == textbook_data['student_borrower'])).fetch()
				#check to see if it has the correct user token
				if student_check:
					new_textbook.student_borrower = textbook_data['student_borrower']

				else:
					#forbidden access
					self.response.write("this id is not associated with your account")
					self.response.set_status(403)
					return
			
			new_textbook.put()
			new_textbook.id = new_textbook.key.urlsafe()
			new_textbook.put()

			textbook_dict = new_textbook.to_dict()
			textbook_dict['self'] = '/textbooks/' + new_textbook.id
			self.response.write(json.dumps(textbook_dict))
			self.response.headers['Content-Type'] = 'application/json'
			self.response.set_status(200)

		else:
			#bad request - title required
			self.response.set_status(404)

	#DELETE
	def delete(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']			
			#self.response.write(userId)
		else:
			#forbidden access
			self.response.set_status(403)
			return

		if id:
			if id == "all":
				all_textbooks = Textbook.query(Textbook.t_token_id == userId).fetch()
				list_textbooks = []
				for textbook in all_textbooks:
					textbook.key.delete()
				self.response.write("all textbooks for "+userId+" has been deleted")
				self.response.set_status(200)
			else:
				textbook_key = ndb.Key(urlsafe=id)
				textbook = textbook_key.get()
				if textbook is not None:

					if textbook.t_token_id == userId:
						textbook.key.delete()
					else:
						#forbidden access
						self.response.write("this id is not associated with your account")
						self.response.set_status(403)
				else:
					self.response.write("this id does not exists")
					self.response.set_status(404)
		else:
			self.response.write("id error")
			self.response.set_status(400)

	#REPLACE
	def put(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']
		else:
			self.response.set_status(403)
			return


		if id:
			textbook_data = json.loads(self.request.body)
			textbook_key = ndb.Key(urlsafe=id)
			textbook = textbook_key.get()
			
			if textbook.t_token_id == userId:
				if 'title' in textbook_data:
					textbook.title = textbook_data['title']

					if 'edition' in textbook_data:
						textbook.edition = textbook_data['edition']
					else:
						textbook.edition = None

					if 'page_count' in textbook_data:
						textbook.page_count = textbook_data['page_count']
					else:
						textbook.page_count = None

					if 'student_borrower' in textbook_data:
						#find the student in the entire Student list
						student_check = Student.query(ndb.AND(Student.s_token_id == userId,Student.id == textbook_data['student_borrower'])).fetch()

						
						if student_check:
							textbook.student_borrower = textbook_data['student_borrower']
						
					else:
						textbook.student_borrower = None

					textbook.put()
					self.response.set_status(200)
					self.response.write("put successful")

				else:
					self.response.write("title is required")
					self.response.set_status(400)

			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
		else:
			self.response.write("id is required")
			self.response.set_status(400)

	#UPDATE
	def patch(self,id=None):
		if 'token_id' in self.request.headers:
			userId = self.request.headers['token_id']
		else:
			self.response.set_status(403)
			return


		if id:
			textbook_data = json.loads(self.request.body)
			textbook_key = ndb.Key(urlsafe=id)
			textbook = textbook_key.get()
			#make sure that the student belongs to this s_token_id
			if textbook.t_token_id == userId:
				if 'title' in textbook_data:
					textbook.title = textbook_data['title']

					if 'edition' in textbook_data:
						textbook.edition = textbook_data['edition']
					

					if 'page_count' in textbook_data:
						textbook.page_count = textbook_data['page_count']
					

					if 'student_borrower' in textbook_data:
						#find the student in the entire Student list
						student_check = Student.query(ndb.AND(Student.s_token_id == userId,Student.id == textbook_data['student_borrower'])).fetch()
						#check to see if it has the correct user token
						if student_check:
							textbook.student_borrower = textbook_data['student_borrower']
											
					textbook.put()
					self.response.set_status(200)
					self.response.write("put successful")

				else:
					self.response.write("title is required")
					self.response.set_status(400)

			else:
				#forbidden access
				self.response.write("this id is not associated with your account")
				self.response.set_status(403)
		else:
			self.response.write("id is required")
			self.response.set_status(400)




class MainPage(webapp2.RequestHandler):
	def get(self):
		flow = OAuth2WebServerFlow(client_id=CLIENT_ID,client_secret=CLIENT_SECRET,scope="email",redirect_uri=REDIRECT_URI)
		#generating new state_value
		
		auth_uri = flow.step1_get_authorize_url()

		StateVar.state_value = str(uuid4())
		
		template_values = {
			#'state':StateVar.state_value,
			'url': auth_uri + "&state=" + StateVar.state_value,
		}
			
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

#PATCH
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
	('/', MainPage),
	('/callback',Callback),
	('/students',StudentHandler),
	('/students/(.*)',StudentHandler),
	('/textbooks',TextbookHandler),
	('/textbooks/(.*)',TextbookHandler),
  

], debug=True)
