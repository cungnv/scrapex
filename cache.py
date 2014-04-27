import os, md5

import common

class Cache(object):
	"""docstring for Cache"""
	def __init__(self, location):		
		self.location = location
		if not os.path.exists(self.location):
			os.makedirs(location)

	def makekey(self, url, post = ''):	
		return common.md5(url + (str(post) if post else '')) + '.htm'

	def write(self, url, data, post='',filename = None):
		key = filename if filename else 	self.makekey(url,post)
		common.putfile(os.path.join(self.location, key), data)

	def read(self, url='', post='', filename= None):
		key = filename if filename else 	self.makekey(url,post)
		return common.getfile(os.path.join(self.location, key))
	def exists(self, url = '', post='', filename = None):
		key = filename if filename else 	self.makekey(url,post)
		
		return os.path.exists(os.path.join(self.location, key))
	def iterate(self):
		for filename in os.listdir(self.location):
			html = self.read(filename=filename)
			yield (filename, html)

		