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
from io import StringIO

import random
import socket
import ssl
import traceback
import requests
import logging

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
		#to avoid using invalid option names
		logger = logging.getLogger(__name__)

		allowed_option_names = 'cookies, proxy, max_redirects, accept_error_codes, merge_headers,cc, ref, ajax, cache_path, show_status_message, use_cache,use_cookie, use_session, use_proxy, user_agent, proxy_file, timeout, delay, retries, bin, headers, filename, contain, dir, parse_log, html_clean, encoding'.replace(' ','').split(',')

		for o in list(options.keys()):
			if o not in allowed_option_names:
				if not options.get('disable_option_name_warning'):
					logger.warn('invalid option name: %s', o)

		self.url = url.replace(' ', '%20')
		
		self.options = options
		
		#update headers
		if 'headers' not in self.options:
			self.options['headers'] = {}

		if 'ref' in self.options:
			self.options['headers']['Referer'] = self.options['ref']
		if self.options.get('ajax') is True:
			self.options['headers']['X-Requested-With'] = 'XMLHttpRequest'

		self.is_normalized = False  
	
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

	def normalize(self, scraper):
		""" normalize this req with using the provided scraper's config """
		if self.is_normalized:
			return self

		self.scraper = scraper  

		#copy scraper-wide options if not set yet   
		self.options = common.combine_dicts(scraper.config, self.options)

		req = self

		self.url = common.normalize_url(self.url)
		# self.url = str(self.url)

		accept_error_codes = req.get('accept_error_codes')
		if accept_error_codes is None:
			accept_error_codes = []
			req.set('accept_error_codes', accept_error_codes)

		#default headers
		user_agent = req.get('user_agent')
		if not user_agent or user_agent == 'random':

			user_agent = agent.random_agent()
		
		headers = requests.structures.CaseInsensitiveDict( {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"User-Agent": user_agent,
			"Accept-Language": "en-us,en;q=0.5",
			"Accept-Encoding": "gzip, deflate",         
			"Connection": "close" #turn off keep-alive
			
		})

			
		#update user-passed in headers

		if req.get('headers') is not None:
			if req.get('merge_headers') is not False:
				
				#merge user defined headers with default headers

				headers.update(req.get('headers')) 

			else:
				#only use user defined headers
				headers = req.get('headers')    


		req.set('headers', headers)

			
		proxy = req.get('proxy') or scraper.proxy_manager.get_proxy(req.url)
		
		req.set('proxy', proxy)
		
		self.is_normalized = True   
		
		return self 


class Client(object):

	def __init__(self, scraper):

		self.scraper = scraper
		
		socket.setdefaulttimeout(self.scraper.config.get('timeout', 45) )

		self.session = requests.Session()


	def load(self, req):
		""" returns a DOM Document"""
		html = self.load_html(req)
		
		doc = Doc(
			html=html, 
			url = req.url, 
			response= html.response)

		doc.success = html.success

		return doc

	def load_html(self, req):

		""" returns a unicode html object """
		cache = self.scraper.cache
		accept_error_codes = req.get('accept_error_codes')
		if accept_error_codes is None:
			accept_error_codes = []

		cacheoptions = dict(url = req.url, data=req.get('data'), json=req.get('json'), params=req.get('params'), filename=req.get('filename'))

		if req.get('use_cache') and cache and cache.exists(cacheoptions):
				
			return self._read_from_cache(cacheoptions)
	
		res = self.request(req)

		html = common.DataItem( res.text or '')

		if (res.status_code == 200 or res.status_code in accept_error_codes) and  cache and req.get('use_cache'):
			self._write_to_cache(html=html, response=res, cacheoptions=cacheoptions)

		html.response = res
		html.success = res.success
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
		
		logger = logging.getLogger(__name__)
		
		req.normalize(self.scraper)

		time.sleep(self.scraper.config['delay'])

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
						
		logger.debug('loading %s', req.url)	
	
		accept_error_codes = req.get('accept_error_codes')
		
		client = requests if req.get('use_session') is False else  self.session
		
		status_code = 0
		
		tries = req.get('retries', 0)


		try:
			
			r = None

			if req.get('post') or req.get('data') or req.get('json'):
				r = client.post(req.url, 
					data = req.get('post') or req.get('data') or None, #backward support
					json=req.get('json') or None, 
					headers = headers, 
					cookies= cookies, timeout = req.get('timeout'), proxies = proxies, verify = False, stream=False)
			else:   
				r = client.get(req.url, params = req.get('params') or None, 
					headers = headers, cookies=cookies, timeout = req.get('timeout'), proxies = proxies, verify = False, stream = False)
			
			status_code = r.status_code

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
			r.success = True
			return r
				

		except Exception as e:            
			
			if tries > 0 and status_code not in accept_error_codes:
				#try to open the request one again  
				logger.debug('data fetching error: %s -- %s', status_code if status_code !=0 else '', req.url)
				req.update({'retries': tries - 1})
				return self.request(req)
			else:
				logger.warn('data fetching error: %s -- %s', status_code if status_code !=0 else '', req.url)    

				#failed
				r.success = False
				return r
		

	def _build_response(self, html, meta):
		response = requests.Response()
		response.url = meta.get('url')
		response.status_code, response.reason = meta.get('status_code'), meta.get('reason')
		response.raw = StringIO( html )
		response.encoding = 'utf-8'
		response.success = meta.get('success')

		return response


	def _read_from_cache(self, options):
		cache = self.scraper.cache

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
		html.success = html.response.success

		return html

	def _write_to_cache(self, html, response, cacheoptions):
		meta = {
				'url': cacheoptions['url'],
				'status_code': response.status_code,
				'reason': response.reason,
				'success': response.success,
			}
		
		self.scraper.cache.write( html=''.join([json.dumps(meta), meta_seperator, html]), options=cacheoptions )   
	

if __name__ == '__main__':
	from . import core
	s = core.Scraper(use_cache=False)
	
	doc = s.load('https://librivox.org/what-i-believe-by-leo-tolstoy/')
	print(doc.x("//title"))
	print(doc.response)
