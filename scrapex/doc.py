#encoding: utf-8

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
import logging

import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
try:
	from urlparse import urljoin
except:
	from urllib.parse import urljoin	

from .node import Node
from . import common

class Doc(Node):
	def __init__(self, url='', html='<html></html>', html_clean=None, response=None):
		logger = logging.getLogger(__name__)      
		if html_clean:
			html = html_clean(html)

		Node.__init__(self, html)
		try:
			self.url = common.DataItem( url )
		except:
			self.url = common.DataItem( url.decode('utf8') )	

		self.response = response
		
		#resolve relative urls
		baseurl = self.x("//base/@href").tostring()
		if not baseurl:
			baseurl = self.url
		try:
			for n in self.q('//a[@href and not(contains(@href, "javascript")) and not(starts-with(@href, "#")) and not(contains(@href, "mailto:"))]'):                  
				if n.href().trim() == '': continue
				n.set('href', urljoin(baseurl, n.get('href').tostring()))

			for n in self.q('//iframe[@src]'):                  
				if n.src().trim() == '': continue
				n.set('src', urljoin(baseurl, n.src()))
		


			for n in self.q('//form[@action]'):                 
				n.set('action', urljoin(baseurl, n.get('action').tostring()))  
			for n in self.q('//img[@src]'):                 
				n.set('src', urljoin(baseurl, n.get('src').tostring()))
		except Exception as e:
			logger.warn('there was error while init the Doc object: %s', self.url)
			logger.exception(e)
							
	def form_data(self, xpath=None):
		data = dict()
		for node in self.q(xpath or "//input[@name and @value]"):
			data.update(dict( ( (node.name(), node.value(),), ) ))

		return data 
	def aspx_vs(self):
		return self.x("//input[@id='__VIEWSTATE']/@value").urlencode() or self.html().sub('__VIEWSTATE|','|').urlencode()
	def aspx_ev(self):
		return self.x("//input[@id='__EVENTVALIDATION']/@value").urlencode() or self.html().sub('__EVENTVALIDATION|','|').urlencode()
	def aspx_prepage(self):
		return self.x("//input[@id='__PREVIOUSPAGE']/@value").urlencode() or self.html().sub('__PREVIOUSPAGE|','|').urlencode() 
