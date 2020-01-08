#encoding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object
import os
import sys
import urllib.request, urllib.parse, urllib.error
import logging


from . import common

class Cache(object):
	"""docstring for Cache"""
	def __init__(self, location):		
		self.location = location
		if self.location and not os.path.exists(self.location):
			os.makedirs(location)

	def make_key(self, options):	
		url = options['url']

		data = options.get('data') or ''
		if isinstance(data, dict):
			data = urllib.parse.urlencode(sorted(data.items()))

		jsondata = options.get('json') or ''
		if isinstance(jsondata, dict):
			data = urllib.parse.urlencode(sorted(jsondata.items()))
		
		params = options.get('params') or ''
		if isinstance(params, dict):
			params = urllib.parse.urlencode(sorted(params.items()))
		
		key = common.md5('{}{}{}{}'.format(url, data, jsondata, params).encode('utf8')) + '.htm'

		return key


	def write(self, html, options):
		logger = logging.getLogger(__name__)
		filename = options.get('filename')

		key = filename if filename else self.make_key(options)

		full_path = os.path.join(self.location, key)

		common.put_file(full_path, html)
					
	def read(self, options):
		filename = options.get('filename')

		key = filename if filename else self.make_key(options)
		return common.get_file(os.path.join(self.location, key))

	def remove(self, options):
		filename = options.get('filename')

		key = filename if filename else self.make_key(options)

		filepath = os.path.join(self.location, key)
		if os.path.exists(filepath):
			os.remove(filepath)

			
	def exists(self, options):
		filename = options.get('filename')

		key = filename if filename else self.make_key(options)
		
		return os.path.exists(os.path.join(self.location, key))
		
	def iterate(self):
		for filename in os.listdir(self.location):
			html = self.read(filename=filename)
			yield (filename, html)

		
			