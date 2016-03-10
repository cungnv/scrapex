import sys, os, time, json, shutil
from scrapex import common

class JsonDB(object):
	""" a simple database based on json format """

	def __init__(self, file_path = 'db.json', keyname=None):
		
		self.file_path = file_path
		self.keyname = keyname

		self.update_count = 0
		self.save_after = 10

		if not os.path.exists(self.file_path):
			#new database
			self.rows = []
			if not keyname:
				raise Exception('keyname is required')


		else:
			#existing database
			data = common.read_json(self.file_path)
			self.keyname = data['keyname']
			self.rows = data['rows']




	def auto_save(self):
		if self.update_count % 	self.save_after == 0:
			self.save()


	def insert(self, r):
		self.update_count +=1


		if self.exists(r[self.keyname]):
			return

		#ready to insert
		self.rows.append(r)


		self.auto_save()


	def get(self, keyvalue):
		for r in self.rows:
			if r[self.keyname] == keyvalue:
				return r #found

		return None #not found		

	def update(self, keyvalue, updatedata):
		self.update_count +=1
		i = 0
		for r in self.rows:
			if r[self.keyname] == keyvalue:
				#found row
				self.rows[i].update(updatedata)
			i+=1	
		self.auto_save()
			
	def delete(self, keyvalue):
		self.update_count +=1
		
		i = 0
		for r in self.rows:
			if r[self.keyname] == keyvalue:
				del self.rows[i] #found
				
				self.auto_save()

				return
			i +=1
					
	def find(self, criteria):
		res = []
		for r in self.rows:
			matched = True
			for k,v in criteria.iteritems():
				if k not in r or r[k] != v: 
					#failed
					matched = False
					break
			if matched:
				res.append(r)
		return res			


	def exists(self, keyvalue):

		for r in self.rows:
			if r[self.keyname] == keyvalue:
				#found
				return True
		
		#not fould		
		return False		

	def save(self):
		data = {'keyname': self.keyname, 'rows': self.rows}
		#backup the existing file
		if os.path.exists(self.file_path):
			shutil.copy2(self.file_path, self.file_path+'.bk')
		common.write_json(self.file_path, data)

		