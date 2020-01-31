#encoding: utf-8

from __future__ import unicode_literals
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()

from builtins import str
from builtins import object

import sys
import re
import html.parser
import copy
from lxml import etree
import lxml.html
from io import StringIO
import logging

from .common import DataItem

logger = logging.getLogger(__name__)
class Node(object):
	lxmlnode = None

	def __init__(self, lxmlnode):

		if 'lxml' in str(type(lxmlnode)):
			self.lxmlnode = lxmlnode

		else:
			#not already a native lxml Node object
			try:					
				if '<?xml' in lxmlnode:
					lxmlnode = re.sub('^\s*<\?xml.*\?>', '', lxmlnode)
					
				self.lxmlnode = lxml.html.fromstring(lxmlnode or '<div></div>')

			except Exception as e:
				# logger.exception(e)
				logger.warn('failed to build node from string: %s -- %s', lxmlnode, type(lxmlnode))
				self.lxmlnode = lxml.html.fromstring('<html></html>')
			
	def set(self, name, value):
		self.lxmlnode.set(name, value)
		return self

	def get(self, name):
		return DataItem(self.lxmlnode.get(name))	

	def html(self):
		try:			
			res = etree.tostring(self.lxmlnode, with_tail=False).decode('utf-8')
			
		except Exception as e:
			#attribute or text node
			res = str(self.lxmlnode.__string__().decode('utf-8'))

		res = res.replace('&#13;', '')	
		if '<nothing/>' == res:
			return DataItem()
			
		return DataItem(res)
	
	def nodevalue(self):
		parser = html.parser.HTMLParser()
		if isinstance(self.lxmlnode, lxml.etree._ElementStringResult) or isinstance(self.lxmlnode, lxml.etree._ElementUnicodeResult):
			value = parser.unescape(self.lxmlnode)
			return DataItem(value)
		else:	
		
			__node = copy.deepcopy(self.lxmlnode)
			etree.strip_tags(__node, '*')			
			value = etree.tostring(__node, with_tail=False).decode('utf8')

			value = re.sub(r'<[^>]*?>','',value)

			value = parser.unescape(value)
			return DataItem(value)

	def text(self):
		return self.nodevalue()

	def extract(self, xpath):
		""" API """
		return self.x(xpath)

	def query(self, xpath):
		""" API """
		return self.q(xpath)

	def x(self, xpath):				
		if not hasattr(self.lxmlnode, 'xpath'): return DataItem()

		node = self.node(xpath)
		if node: 
			res = node.nodevalue()							
		else: 
			res = DataItem()			
		return res

	def q(self, xpath):
		"""find all nodes"""

		res = NodeList()
		try:			
			for e in self.lxmlnode.xpath(xpath):								
				res.append(Node(e))
		except Exception:
			pass

		return res

	def node(self, xpath):
		"""get a single node"""
		
		res = self.q(xpath)
		
		if res: return res[0]
		else: return Node('<nothing></nothing>')

	def remove(self, xpath):
		"""remove all child nodes from current node"""
		for child in self.q(xpath):			
			child.lxmlnode.getparent().remove(child.lxmlnode)
		return self	

	#create some common shortcuts	
	def href(self):
		try:
			return self.x('./@href')
		except Exception:
			return DataItem()
	def src(self):
		try:
			return self.x('./@src')
		except Exception:
			return DataItem()	
	def value(self):
		try:
			return self.x('./@value')
		except Exception:
			return DataItem()		
	def id(self):
		try:
			return self.x('./@id')
		except Exception:
			return DataItem()		
	def name(self):
		try:
			return self.x('./@name')
		except Exception:
			return DataItem()		
			

	def contains(self, something):
		return something in self.html()

	def insert_line_breaks(self):
		for _node in self.q(".//*"):
			node = _node.lxmlnode
			if node.tag.lower() in ['p','li','br']:
				
				if node.tag.lower() == 'br':
					newline = etree.Element('newline')
					newline.text = '\n'
					node.append(newline)
				else:
					# newline = etree.SubElement(node, 'newline')
					# newline.text = '\n'		
					newline = etree.Element('newline')
					newline.text = '\n'
					node.append(newline)
		return self		
	

class NodeList(list):	
	def __init__(self, *args):
		list.__init__(self, *args)

	def len(self):
		return len(self)
	def join(self, sep = ', ', pre=''):
		values = []
		for node in self:
			if node.nodevalue().trim().tostring():
				values.append(node.nodevalue().trim())
		
		return	DataItem(pre + sep.join(values)) if values else DataItem()
