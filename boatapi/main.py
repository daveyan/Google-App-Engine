
from google.appengine.ext import ndb
import webapp2
import time
import json
import random

#PATCH - reference - http://stackoverflow.com/questions/16280496/patch-method-handler-on-google-appengine-webapp2
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods


class Boat(ndb.Model):
	id = ndb.StringProperty()
	#https://piazza.com/class/j11uzyv2wmh5pl?cid=42 boat name required
	name = ndb.StringProperty(required=True)
	type = ndb.StringProperty()
	length = ndb.IntegerProperty()
	at_sea = ndb.BooleanProperty()

class Slip(ndb.Model):
	id = ndb.StringProperty()
	#https://piazza.com/class/j11uzyv2wmh5pl?cid=42 slip number required
	number = ndb.IntegerProperty(required=True)
	current_boat = ndb.StringProperty()
	arrival_date = ndb.StringProperty()
	departure_history = ndb.JsonProperty(repeated=True)
		

class BoatHandler(webapp2.RequestHandler):
	#1. Add
	def post(self):
		
		boat_data = json.loads(self.request.body)
		if 'name' in boat_data:
			new_boat = Boat(name = boat_data['name'],at_sea = True)
			#check to see if there is a type
			if 'type' in boat_data:
				new_boat.type = boat_data['type']
			else:
				new_boat.type = None
			#check to see if there is a length
			if 'length' in boat_data:
				new_boat.length = boat_data['length']
			else:
				new_boat.length = None

			new_boat.put()	
			#create an id for the boat
			new_boat.id = new_boat.key.urlsafe()
			
			new_boat.put()
			
			boat_dict = new_boat.to_dict()
			boat_dict['self'] = "/boats/" + new_boat.id

			self.response.write(json.dumps(boat_dict))
			self.response.headers['Content-Type'] = 'application/json'
													
		else:
			#bad request - name required
			self.response.set_status(400)
			self.response.write("name required")
			return

	#2. Delete
	def delete(self, id=None):
		if id:

			boat_key = ndb.Key(urlsafe=id)
			boat = boat_key.get()
			if boat:
				#boat is at sea - safe to delete
				if boat.at_sea:
					boat.key.delete()
					self.response.write("Deleted")
				#boat is in the slip
				else:
					#find the slip the boat is currently in
					boat_slip = Slip.query(Slip.current_boat == id)
					if boat_slip:
						#slip = boat_slip.get()
						#remove the boat
						boat_slip.current_boat = ""
						boat_slip.arrival_date = ""
					boat_slip.put()
					boat.key.delete()
					self.response.write("Deleted")
			else:
				self.response.set_status(400)
				return

			
		#id is required for deletion
		else:
			self.response.write("id error")
			self.response.set_status(400)

	#3. Modify
	def patch(self, id=None):
		if id:
			boat_data = json.loads(self.request.body)
			boat_key = ndb.Key(urlsafe=id)
			boat = boat_key.get()

			#check for valid id
			if boat:
				#make sure there is a name 
				if 'name' in boat_data:
					boat.name = boat_data['name']
					if 'type' in boat_data:
						boat.type = boat_data['type']

					if 'length' in boat_data:
						boat.length = boat_data['length']

					boat.id = id

					if 'at_sea' in boat_data:
	 					#place boat on the sea
						if boat_data['at_sea'] == True:
							#find the slip the boat is docked in
							if not boat.at_sea:
								boat_slip = Slip.query(Slip.current_boat == id).fetch()
								#remove boat from the slip
								boat_slip.current_boat = ""
								boat_slip.arrival_date = ""
								#append time and id to departure_history
								dep_history = {}
								dep_history['departure_date'] = time.ctime()
								dep_history['departure_boat'] = id
								boat_slip.departure_history = dep_history
								boat_slip.put()
								self.response.write('slip emptied')
								boat.at_sea = True
								self.response.write('boat on sea')


							else:
								#boat already in the sea. do nothing
								pass
						#place boat in slip
						
						if boat_data['at_sea'] == False:
							#find an open slip and place it in
							all_slip = Slip.query().fetch()
							
							isEmpty=False
							for slip in all_slip:
								if slip.current_boat == "":
									slip.current_boat = id
									slip.arrival_date = time.ctime()
									boat.at_sea = boat_data['at_sea']
									isEmpty=True
									break
								
							if not isEmpty:
								#does not change the value of at_sea
								self.response.write('no open slips')


						else:
							
							pass

					boat.put()

					#update entity
					boat_dict = boat.to_dict()
					boat_dict['self'] = '/boat/' + boat_key.urlsafe()
					self.response.write(json.dumps(boat_dict))
					self.response.headers['Content-Type'] = 'application/json'



				else:
					self.response.set_status(400)
					self.response.write("invalid name")

			else:
				self.response.set_status(400)
				self.response.write("invalid boat")
		#id is required for patch
		else:
			self.response.set_status(400)

	#4. Replace
	def put(self, id=None):
		if id:
			boat_data = json.loads(self.request.body)
			boat_key = ndb.Key(urlsafe=id)
			boat = boat_key.get()

			#check for valid id
			if boat:
				#make sure there is a name 
				if boat_data['name']:
					boat.name = boat_data['name']

					#if there is no type. set it to None
					if 'type' in boat_data:
						boat.type = boat_data['type']
					else:
						boat.type = None

					#if there is no type. set it to None
					if 'length' in boat_data:
						boat.length = boat_data['length']
					else:
						boat.length = None

					boat.id = id

					#if there is not at_sea. set it to True
					if 'at_sea' in boat_data:
						#place boat on the sea
						if boat_data['at_sea'] == True:
							#find the slip the boat is docked in
							if not boat.at_sea:
								boat_slip = Slip.query(Slip.current_boat == id).fetch()
								#remove boat from the slip
								boat_slip.current_boat = ""
								boat_slip.arrival_date = ""
								#append time and id to departure_history
								dep_history = {}
								dep_history['departure_date'] = time.ctime()
								dep_history['departure_boat'] = id
								boat_slip.departure_history = dep_history
								boat_slip.put()
								self.response.write('slip emptied')
								boat.at_sea = True
								self.response.write('boat on sea')


							else:
								#boat already in the sea. do nothing
								pass
						#place boat in slip
						
						if boat_data['at_sea'] == False:
							#find an open slip and place it in
							all_slip = Slip.query().fetch()
							
							isEmpty=False
							for slip in all_slip:
								if slip.current_boat == "":
									slip.current_boat = id
									slip.arrival_date = time.ctime()
									boat.at_sea = boat_data['at_sea']
									isEmpty=True
									break
								
							if not isEmpty:
								#does not change the value of at_sea
								self.response.write('no open slips')


						else:
							pass
					
					else:
						boat.at_sea = True

					boat.put()

					#update entity
					boat_dict = boat.to_dict()
					boat_dict['self'] = '/boat/' + boat_key.urlsafe()
					self.response.write(json.dumps(boat_dict))
					self.response.headers['Content-Type'] = 'application/json'


				else:
					self.response.set_status(400)

			else:
				self.response.set_status(400)
		#id is required for patch
		else:
			self.response.set_status(400)

	#5. View		
	def get(self, id=None):
		#return a specific boat based on the id
		if id:

			boat_key = ndb.Key(urlsafe=id)
			boat = boat_key.get()
			#check if the id is valid
			if boat:
				
				boat_dict = boat.to_dict()
				boat_dict['self'] = '/boats/'+ id
				#convert the json object into a string for the response
				self.response.write(json.dumps(boat_dict))
				self.response.headers['Content-Type'] = 'application/json'
			#error
			else: 
				self.response.write("id invalid")
				self.response.set_status(400)
				return
		#get all boats	
		else:
			all_boats = Boat.query().fetch()
			list_boats = []
			for boat in all_boats:
				boat_dict = boat.to_dict()
				list_boats.append(boat_dict)
			self.response.write(json.dumps(list_boats))	
			self.response.headers['Content-Type'] = 'application/json'

class SlipHandler(webapp2.RequestHandler):
	#1. Add
	def post(self):

		slip_data = json.loads(self.request.body)

		if 'number' in slip_data:
			new_slip = Slip(number = slip_data['number'])
			#all created new slips are empty
			new_slip.current_boat = ""
			new_slip.arrival_date = ""
			new_slip.departure_history = []

			new_slip.put()
			#create and id for the slip
			new_slip.id = new_slip.key.urlsafe()

			new_slip.put()
			slip_dict = new_slip.to_dict()
			slip_dict['self'] = '/slips/' + new_slip.id

			self.response.write(json.dumps(slip_dict))
			self.response.headers['Content-Type'] = 'application/json'

		else:
			#bad request number is required
			self.response.set_status(400)

	#2. Delete
	def delete(self, id=None):
		if id:

			slip_key = ndb.Key(urlsafe=id)
			slip = slip_key.get()

			if slip:
				
				#check if there is a boat in the slip
				if slip.current_boat:
					#boat = Boat.query(Boat.id == slip.current_boat)
					#put the boat back into the sea
					#boat.at_sea = True
					#boat.put()

					slip.key.delete()
					self.response.write('Deleted')
				#no boat in the slip
				else:
					slip.key.delete()
					self.response.write('Deleted')
			else:
				
				self.response.set_status(400)
				return
		#id is required for deletion
		else:
			self.response.set_status(400)
			

	#3. Modify	
	def patch(self, id=None):
		if id:
			slip_data = json.loads(self.request.body)
			slip_key = ndb.Key(urlsafe=id)
			slip = slip_key.get()

			if slip:
				#check to see if there is a number
				if 'number' in slip_data:
					slip.number = slip_data['number']
				else:
					self.response.set_status(400)
					return

				slip.id = id
				
				#see if there is a boat data
				if 'current_boat' in slip_data:
					#there is no boat
					if slip.current_boat == "":
						slip.current_boat = slip_data['current_boat']
					#same boat - no issues	
					if slip.current_boat == slip_data['current_boat']:
						pass

					#if the slip is occupied the server should return an Error 403 Forbidden message
					if not slip.current_boat == slip_data['current_boat']:
						self.response.write('slip is occupied')
						self.response.set_status(403)
						return

				if 'arrival_date' in slip_data:
					slip.arrival_date = slip_data['arrival_date']

				slip.put()

				slip_dict = slip.to_dict()
				slip_dict['self'] = '/boat/' + slip_key.urlsafe()
				self.response.write(json.dumps(slip_dict))
				self.response.headers['Content-Type'] = 'application/json'

			else:
				self.response.write("slip id ")
				self.response.set_status(400)
				return
		#id is required in order to patch
		else:
			self.response.write("id error ")
			self.response.set_status(400)

	#4. Replace
	def put(self, id=None):
			if id:
				slip_data = json.loads(self.request.body)
				slip_key = ndb.Key(urlsafe=id)
				slip = slip_key.get()

				if slip:
					#check to see if there is a number
					if 'number' in slip_data:
						slip.number = slip_data['number']
					else:
						self.response.set_status(400)
						return

					slip.id = id
					#see if there is a boat data

					if 'current_boat' in slip_data:
						#there is no boat
						if slip.current_boat == "":
							slip.current_boat = slip_data['current_boat']
						#same boat - no issues
						if slip.current_boat == slip_data['current_boat']:
							pass

						#if the slip is occupied the server should return an Error 403 Forbidden message
						if not slip.current_boat == slip_data['current_boat']:
							self.response.write('slip is occupied')
							self.response.set_status(403)
							return
					#there is no current boat
					else:
						slip.current_boat = ""

					if 'arrival_date' in slip_data:
						slip.arrival_date = slip_data['arrival_date']
					else:
						slip.arrival_date = ""


					slip.put()

				else:
					self.response.set_status(400)
					return
			#id is required in order to patch
			else:
				self.response.set_status(400)

	#5. View
	def get(self, id=None):
			#return a specific slip based on the id
			if id:
				slip_key = ndb.Key(urlsafe=id)
				slip = slip_key.get()
				#check if the id is valid
				if slip:
					slip_dict = slip.to_dict()
					slip_dict['self'] = '/slips/'+id
					self.response.write(json.dumps(slip_dict))
					self.response.headers['Content-Type'] = 'application/json'
				else:
					self.response.set_status(400)
					self.response.write("id error")
			#return all slips
			else:
				all_slips = Slip.query().fetch()
				list_slips = []
				for slip in all_slips:
					slip_dict = slip.to_dict()
					list_slips.append(slip_dict)
				self.response.write(json.dumps(list_slips))
				self.response.headers['Content-Type'] = 'application/json'



class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write("REST Planning and Implementation\nDavid Yan (Yanda)\n")


app = webapp2.WSGIApplication([
	('/', MainPage),
	('/boats',BoatHandler),
	('/boats/(.*)', BoatHandler),
	('/slips',SlipHandler),
	('/slips/(.*)', SlipHandler),
], debug=True)
