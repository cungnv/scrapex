#encoding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
from builtins import next
from builtins import str
from past.builtins import basestring
from builtins import object
from past.utils import old_div
import os
import sys
import time
import re
import atexit
import logging

from .node import Node
from .worker import Worker
from .http import Request
from .cache import Cache
from . import (http, common)
from .proxy import ProxyManager

logger = logging.getLogger(__name__)


class Scraper(object):
	

	def __init__(self, **options):		

		_dir = os.path.dirname(sys.executable) if 'python' not in sys.executable.lower() else os.path.dirname( os.path.join( os.getcwd(), sys.argv[0] ) )
		

		self.config = dict(
			dir = _dir,			
			use_cache = False, 
			cache_path = "cache",
			use_proxy = True, 			
			use_session = False,
			proxy_file = None,
			proxy_url = None,
			timeout = 45,
			delay = 0.1,
			retries = 0,
			max_redirects = 3,
			greeting = False,
			)


		
		self.config.update(options)

		if self.config['autoflush']:
			atexit.register(self.flush)


		if self.config['greeting']:
			print('scrape started')
			atexit.register(self.last_message)
		
		
		#backfowrd support
		if 'use_cookie' in options:
			self.config['use_session'] = options['use_cookie']


		#expose important attributes
		self.dir = self.config.get('dir')
		if not os.path.exists(self.dir): os.makedirs(self.dir)		

		
		#create cache object	
		cache_path = os.path.join(self.dir, self.config['cache_path'])	
	
		self.cache = Cache(cache_path)
			
		self.proxy_manager = ProxyManager(
			proxy_file= self.join_path( self.config.get('proxy_file') ) if self.config.get('proxy_file') else None, 

			proxy_url= self.config['proxy_url'] )
		
		self.client = http.Client(scraper=self)

		
		#set flags
		self.writingflag = False

		#init the output db
		self.outdb = {}

		self._time_start = time.time()

		
	def get_stats(self):
		try:
			self.client.stats['average_seconds_per_request'] = round(self.client.stats['total_request_seconds'] / self.client.stats['total_requests'], 1)
		except Exception as e:
			pass

		return self.client.stats		

	def join_path(self, filename):
		return os.path.join(self.dir, filename)
	def read_lines(self, filename):
		return common.read_lines(self.join_path(filename))	

	def write_json(self, filename, data):
		common.write_json(self.join_path(filename), data)
		return self
	def read_json(self, filename):
		return common.read_json(self.join_path(filename))

	def clear_cookies(self):
		self.client.session.cookies.clear()
		return self

	
	def load(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load(Request(url = url, post = post, **options))

	def request(self, url, post=None, **_options):
		"""
		returns original requests' response, without building Doc object

		"""
		
		options = common.combine_dicts(self.config, _options)
		return self.client.request(Request(url = url, post = post, **options))
	

	def load_html(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load_html(Request(url = url, post = post, **options))
	
	def load_json(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load_json(Request(url = url, post = post, **options))
			
	def  save_link(self, url, filename, dir='images', **_options):
		""" backward supports """
		
		return self.download_file(url, filename, dir, **_options)

	def download_file(self, url, filename, dir='images', **_options):
		
		dir_path = self.join_path(dir)
		if not os.path.exists(dir_path):
			try:
				os.makedirs(dir_path)
			except:
				pass	

		path = os.path.join(self.dir, dir, filename)
		
		if(os.path.exists(path)):
			return (True, 200)
		else:
			#start downloading the file
			options = common.combine_dicts(self.config, _options)		
			
			res = self.client.request(http.Request(url=url, **options))	
					
			if res.status_code == 200:
				common.put_bin(path, res.content)
				return (True, res.status_code)
			else:
				return (False, res.status_code)


	

	
        		
	def flush(self):
		if not hasattr(self, 'outdb'):
			#nothing to flush out
			return

		for filepath in list(self.outdb.keys()):
			trackingobj = self.outdb.get(filepath)
			if trackingobj['format'] == 'csv':
				continue
			elif trackingobj['format'] == 'xls':
				from . import excellib
				excellib.save_xls(filepath, trackingobj.data)
			elif trackingobj['format'] == 'xlsx':
				from . import excellib
				excellib.save_xlsx(filepath, trackingobj['data'])	

				
		#clear the db
		self.outdb = {}

	def last_message(self):
		
		print('scrape finished')

	def save(self, record, filename = 'result.csv', max=None, keys=[], id = None, headers = [], remove_existing_file = True, always_quoted=True):		
		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
			
		path = os.path.join(self.dir, filename)
		format = common.DataItem(path).subreg('\.([a-z]{2,5})$', re.I|re.S).lower()

		if not self.outdb.get(path):
			if os.path.exists(path):
				if remove_existing_file:						
					os.remove(path)		
					
			self.outdb.update({ path: dict(cnt=0, data=[], ids = [], format = format)})	

		trackingobj = self.outdb.get(path)
		if keys or id:
			id = id or "".join([ str( record[record.index(key) + 1 ] ) for key in keys])
			if id in trackingobj.ids:
				self.writingflag = False
				return
			else:
				trackingobj['ids'].append(id)
		
		trackingobj['cnt'] += 1

		if format == 'csv':				
			#for csv format, save to file immediately	
			common.save_csv(path, record, always_quoted=always_quoted)
		elif format in ['xls', 'xlsx']:
			#save for later
			trackingobj['data'].append(record)
		if max and trackingobj['cnt'] == max:
			self.flush() #save output files and quit
			os._exit(1)	

		#free the flag
		self.writingflag = False
	def append_line(self, filename, line, dedup=False):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
		path = self.join_path(filename)					

		if dedup:
			if not hasattr(self,'_data_lines'):				
				self._data_lines = []

			if common.md5(line) not in self._data_lines:								
				self._data_lines.append(common.md5(line))							
				common.append_file(path, line+'\r\n')
		else:
			common.append_file(path, line+'\r\n')
					

		#free the flag
		self.writingflag = False	

	def put_file(self, filename, data):
		common.put_file(self.join_path(filename), data)	
		return self

	def read_csv(self, path, restype='list', encoding='utf8', line_sep='\r\n'):
		"""
		read a csv file into a list

		@restype: list or dict

		"""	
		res = []
		
		for r in common.read_csv(path=self.join_path(path),restype=restype, encoding=encoding, line_sep=line_sep):
			res.append(r)

		return res	
	