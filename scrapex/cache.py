import os, sys, md5, urllib, logging

from scrapex import common

class Cache(object):
	"""docstring for Cache"""
	def __init__(self, location):		
		self.location = location
		if self.location and not os.path.exists(self.location):
			os.makedirs(location)

	def make_key(self, url, post = ''):	
		#normalise the post
		if post and isinstance(post, common.MyDict):
			post = post.dict()
		if post and isinstance(post, dict):
			post = urllib.urlencode(sorted(post.items()))

		return common.md5((url + (post or '')).encode('utf8')) + '.htm'

	def write(self, url='', data='', post='',file_name = None):
		logger = logging.getLogger(__name__)

		key = file_name if file_name else 	self.make_key(url,post)
		full_path = os.path.join(self.location, key)
		try:
			if not os.path.exists(full_path):
				common.put_file(full_path, data)
		except Exception as e:
			logger.exception(e)
					
	def read(self, url='', post='', file_name= None):
		key = file_name if file_name else 	self.make_key(url,post)
		return common.get_file(os.path.join(self.location, key))

	def remove(self, url='', post='', file_name= None):
		key = file_name if file_name else 	self.make_key(url,post)
		filepath = os.path.join(self.location, key)
		if os.path.exists(filepath):
			os.remove(filepath)

			
	def exists(self, url = '', post='', file_name = None):
		key = file_name if file_name else 	self.make_key(url,post)
		
		return os.path.exists(os.path.join(self.location, key))
		
	def iterate(self):
		for file_name in os.listdir(self.location):
			html = self.read(file_name=file_name)
			yield (file_name, html)

		
