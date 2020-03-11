#encoding: utf-8

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import os
import time
import json
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import io
from io import StringIO
from collections import OrderedDict
import random
import socket
import ssl
import traceback
import requests
import logging
import weakref


from . import (common, agent)
from .node import Node
from .proxy import (ProxyManager, Proxy)
from .doc import Doc

try:
	_create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
	# Legacy Python that doesn't verify HTTPS certificates by default
	pass
else:
	# Handle target environment that doesn't support HTTPS verification
	ssl._create_default_https_context = _create_unverified_https_context

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


meta_seperator = '=======META======'

logger = logging.getLogger(__name__)



class Request(object):  
	""" Represents a http request """

	def __init__(self, url, **options):        
		
		self.url = url.replace(' ', '%20')
		
		self.options = options
		
		#update headers
		if 'headers' not in self.options:
			self.options['headers'] = {}

		if 'ref' in self.options:
			self.options['headers']['Referer'] = self.options['ref']
		if self.options.get('ajax') is True:
			self.options['headers']['X-Requested-With'] = 'XMLHttpRequest'

	
	def __getitem__(self, key):
		return self.get(key)

	def get(self, name, default = None):
		return self.options.get(name, default)
	def set(self, name, value):
		self.options[name]= value
		return self

	def update(self, dict2):
		self.options.update(dict2)
		return self

	def optimise(self, proxy_manager):
		
		self.url = common.normalize_url(self.url)

		#default headers
		user_agent = self.get('user_agent')
		if not user_agent or user_agent == 'random':

			user_agent = agent.random_agent()
		
		
		proxy = self.get('proxy') or proxy_manager.random_proxy()
		
		self.set('proxy', proxy)

		#default base headers
		headers = requests.structures.CaseInsensitiveDict(OrderedDict([
			("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
			("User-Agent", user_agent),
			("Accept-Language", "en-us,en;q=0.5"),
			("Accept-Encoding", "gzip, deflate"), 

			("Connection", "close"),
			
		]))

		if not self.get('proxy') or self.get('use_proxy') is False or len(proxy_manager.proxies)>1:
			#use keep-alive connection
			headers['Connection'] = 'keep-alive'

		#update user-passed headers
		if self.get('headers') is not None:
			headers.update(self.get('headers')) 

		self.set('headers', headers)

		return self 


class Client(object):

	def __init__(self, scraper):

		self.config = scraper.config
		self.cache =  scraper.cache
		self.proxy_manager = scraper.proxy_manager
		
		self.session = requests.Session()
		self.session_nocookies = requests.Session()

		#clear default headers
		self.session.headers.clear()
		self.session_nocookies.headers.clear()

		self.stats = {
			'total_requests': 0,
			'success_requests': 0,
			'failed_requests': 0,
			'failed_requests_by_status_code': {},
			'finally_failed_requests': 0,
			'retry_count': 0,
			'total_request_seconds': 0,
			'average_seconds_per_request': None,


		}
	
	def load(self, req):
		""" returns a DOM Document"""
		html = self.load_html(req)
		
		doc = Doc(
			html=html, 
			url = req.url, 
			response= html.response)

		return doc

	def load_html(self, req):

		""" returns a unicode html object """
		cache = self.cache
		
		cacheoptions = dict(url = req.url, data=req.get('data'), json=req.get('json'), params=req.get('params'), filename=req.get('filename'))

		if req.get('use_cache') and cache and cache.exists(cacheoptions):
				
			return self._read_from_cache(cacheoptions)
	
		res = self.request(req)

		html = common.DataItem( res.text or '')

		if res.status_code == 200 and  cache and req.get('use_cache'):
			self._write_to_cache(html=html, response=res, cacheoptions=cacheoptions)

		html.response = res
		
		return html 

		
	def load_json(self, req):
		""" returns a json object """
		data = self.load_html(req)
		try:
			return json.loads(data)

		except:
			logger.exception('json decode error for url: %s --  post: %s', req.url, req.post or '')
			return None 

	
	def request(self, req):
		
		req.optimise(self.proxy_manager)

		maxtries = 1 + (req.get('retries') or 0)

		tries = 0
		while True:
			tries += 1
			if tries>maxtries:
				raise Exception('max retries exceeded')

			_start_time = time.time()
			time.sleep(self.config['delay'])

			headers = req.get('headers')
			cookies = req.get('cookies') or {}
			proxy = req.get('proxy')

			proxies = None
			if proxy and req.get('use_proxy') is not False:
				
				logger.debug('proxy: {}:{}'.format(proxy.host, proxy.port))

				proxies = {
							'http': 'http://{0}'.format(proxy.full_address),
							'https': 'http://{0}'.format(proxy.full_address)
						}
							
			logger.debug('loading (try# %s) %s', tries, req.url)
			
			client = None
			if req.get('use_session'):
				client = self.session

			else:
				self.session_nocookies.cookies.clear()
				client = self.session_nocookies

			try:

				
				r = None
				#by default, method is automatically detected
				method = req.get('method') or None
				if not method:
					if req.get('post') or req.get('data') or req.get('json'):
						method = 'POST'
					else:
						method = 'GET'	
				
				r = client.request(
						url= req.url, 
						
						method = method,
						
						params = req.get('params') or None,

						data = req.get('post') or req.get('data') or None, #backward support
						json=req.get('json') or None, 
						
						headers = headers, 
						cookies= cookies, 
						timeout = req.get('timeout'), 
						proxies = proxies, 
						verify = req.get('verify') or False, 
						stream= req.get('stream') or False
						)

				r.raise_for_status()

				#verify data
				if req.get('contain'):
					html = r.text
					if req.get('contain') not in html:
						raise Exception("invalid html, not contain: {0}".format(req.get('contain')))

				if req.get('contain_xpath'):
					html = r.text
					doc = Doc(html=html, url=req.url)

					if doc.q(req.get('contain_xpath')):

						raise Exception("invalid html, not contain_xpath: {0}".format(req.get('contain_xpath')))
				
				#success
				self.stats['success_requests'] += 1
				return r
			
			except requests.exceptions.RequestException as e:
				status_code = None
				reason = None
				try:
					status_code = e.response.status_code
					reason = e.response.reason
				except:
					pass

				self.stats['failed_requests'] += 1

				if status_code not in self.stats['failed_requests_by_status_code']:
					self.stats['failed_requests_by_status_code'][status_code] = 1
				else:
					self.stats['failed_requests_by_status_code'][status_code] += 1	
				
				
				if tries < maxtries and status_code not in [404]:
					#try to open the request one again 
					self.stats['retry_count'] += 1
					logger.info('request error: %s (%s) -- url: %s', status_code, reason, req.url)
					logger.info('retry request: %s', req.url)
					req.update({'proxy': self.proxy_manager.random_proxy()})
				else:	
					#for other reasons, just raise the exception
					self.stats['finally_failed_requests'] += 1
					logger.warn('request failed: %s (%s) -- url: %s', status_code, reason, req.url)
					raise e
				
			finally:
				
				self.stats['total_request_seconds'] += time.time() - _start_time
				self.stats['total_requests'] += 1

	def _build_response(self, html, meta):

		response = requests.Response()
		response.url = meta.get('url')
		response.status_code, response.reason = meta.get('status_code'), meta.get('reason')
		response.raw = io.BytesIO(html.encode('utf-8'))
		response.encoding = 'utf-8'
		
		return response


	def _read_from_cache(self, options):
		cache = self.cache

		cachedata = cache.read(options).split(meta_seperator)
		
		cachedhtml = None
		

		if len(cachedata)==2:
			cachedhtml = cachedata[1]
			meta = json.loads( cachedata[0] )
			
		else:
			meta = {}
			cachedhtml = cachedata[0]
		
		html = common.DataItem(cachedhtml)  
		html.response = self._build_response(html,meta)
		

		return html

	def _write_to_cache(self, html, response, cacheoptions):
		meta = {
				'url': cacheoptions['url'],
				'status_code': response.status_code,
				'reason': response.reason,
				
			}
		
		self.cache.write( html=''.join([json.dumps(meta), meta_seperator, html]), options=cacheoptions )   
	

if __name__ == '__main__':
	from . import core
	s = core.Scraper(use_cache=False)
	
	doc = s.load('https://librivox.org/what-i-believe-by-leo-tolstoy/')
	print(doc.x("//title"))
	print(doc.response)
