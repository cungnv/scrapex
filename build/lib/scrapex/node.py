import re, HTMLParser, copy, sys
from lxml import etree
import lxml.html
from StringIO import StringIO

from scrapex.common import DataItem
from scrapex import common

class Node(object):
	lxmlnode = None

	def __init__(self, lxmlnode):
		if 'lxml' not in str(type(lxmlnode)):			
			try:					
				if '<?xml' in lxmlnode:
					lxmlnode = re.sub('^\s*<\?xml.*\?>', '', lxmlnode)
					
				self.lxmlnode = lxml.html.fromstring(lxmlnode or '<nothing/>')

			except Exception, e:
				#print e
				self.lxmlnode = lxml.html.fromstring('<html></html>')
				
		else:				
			self.lxmlnode = lxmlnode

	def set(self, name, value):
		self.lxmlnode.set(name, value)
		return self

	def get(self, name):
		return DataItem(self.lxmlnode.get(name))	

	def html(self):
		try:			
			res = etree.tostring(self.lxmlnode, with_tail=False)
			
		except Exception, e:
			#attribute or text node
			res = unicode(self.lxmlnode)
		res = res.replace('&#13;', '')	
		if '<nothing/>' == res:
			return DataItem()
			
		return DataItem(res)
	
	def nodevalue(self):
		parser = HTMLParser.HTMLParser()
		try:
			__node = copy.deepcopy(self.lxmlnode)
			etree.strip_tags(__node, '*')			
			res = etree.tostring(__node, with_tail=False)
			res = re.sub(r'<[^>]*?>','',res)			
			res = parser.unescape(res)			
		except Exception, e:
			#attribute or text node
			res = parser.unescape(self.lxmlnode)

		return DataItem(res)		


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
