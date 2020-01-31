#encoding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import os
import urllib.parse
import time
import random
import base64
import logging

from . import common

class Proxy(object):
	def __init__(self, host, port, proxy_auth = None):
		self.host = host
		self.port = int(port)
		self.proxy_auth = proxy_auth
		
		self.auth_header = b'Basic ' + base64.b64encode(self.proxy_auth.encode('utf8')) if self.proxy_auth else None

		self.full_address = ( '%s@%s:%s' % (self.proxy_auth, self.host, self.port) ) if self.proxy_auth else ('%s:%s' % (self.host, self.port))

	def __str__(self):
		return '%s:%s' % (self.host, self.port)

class ProxyManager(object):
	
	""" for proxy rotation controlling """

	def __init__(self, proxy_file=None, proxy_url=None):      
		self.proxy_file = proxy_file
		self.proxy_url = proxy_url
		
		self.proxies = []

		self.load_proxies()

		self.session_proxy = None #if set, always use this project intead of radom one

	def parse_proxy(self, proxy_line, proxy_auth=None):
		proxy = proxy_line

		if len(proxy.split(':')) == 2:

			return Proxy(host=proxy.split(':')[0], port=proxy.split(':')[1], proxy_auth=proxy_auth)	
			
		#support proxy in ip:port:user:pass
		if len(proxy.split(':')) == 4:
			proxy = proxy.split(':')
			return Proxy(host=proxy[0], port=proxy[1], proxy_auth='%s:%s' % (proxy[2], proxy[3]))
		
		raise Exception('failed to parse proxy: %s', proxy) 
		
	
	def load_proxies(self):     
		
		if self.proxy_file:
			proxy_file = self.proxy_file
			if not os.path.exists(proxy_file):
				raise Exception('proxy_file not found: {0}'.format(proxy_file))
			
			proxy_auth = None	
			for line in common.read_lines(proxy_file):
				if 'proxy_auth' in line:
					proxy_auth = common.DataItem(line).rr('proxy_auth\s*=\s*').trim()
					continue

				#support tab, commas separator as well
				line = line.replace('\t',':').replace(',',':')  
				self.proxies.append(self.parse_proxy(line, proxy_auth))     

		elif self.proxy_url:
			
			netloc = urllib.parse.urlparse(self.proxy_url).netloc
			parts = netloc.split('@')

			if len(parts)==2:
				proxy_auth = parts[0]
				host, port = parts[1].split(':')
				proxy = Proxy(host=host, port=port, proxy_auth=proxy_auth)
				self.proxies.append(proxy)
			else:
				host, port = parts[0].split(':')
				proxy = Proxy(host=host, port=port, proxy_auth=None)
				self.proxies.append(proxy)
		

		return self 

	def random_proxy(self):
		if not self.proxies:
			return None

		return random.choice( self.proxies )    


	def get_proxy(self, url=None):

		return self.session_proxy or self.random_proxy()
