#encoding: utf-8

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object
import hashlib
import os
import sys
import copy
import codecs
import re
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import json
import string
import threading
import io
import csv
import logging
import pickle
import random
import time
from queue import Queue
from collections import OrderedDict

from html.parser import HTMLParser
from openpyxl import Workbook


logger = logging.getLogger()



def parse_cookies(cookieline):
	
	cookies = {}
	for pair in cookieline.split('; '):

		parts = pair.strip().split('=')

		name = parts.pop(0)
		value = '='.join(parts)
		cookies[name] = value
			

	return cookies	


def convert_csv_to_xlsx(csv_file_path, xlsx_file_path, max_num_of_rows=None):
	csv.field_size_limit(sys.maxsize)
	if not max_num_of_rows:
		# put all rows into a single xlsx file
		wb = Workbook()
		sheet = wb.active

		i = 0
		for r in read_csv(csv_file_path):
			i+= 1

			sheet.append(r)


		wb.save(xlsx_file_path)	
	else:
		#use multiple xlsx file
		fileindex = 0
		headers = None
		cnt_rows = 0

		i = 0
		for r in read_csv(csv_file_path):
			
			i+= 1
			if i == 1:
				headers = r
				continue
			
			assert len(r) == len(headers), 'invalid row'

				
			if cnt_rows == 0:

				fileindex += 1
				
				xlsx_file = xlsx_file_path.replace('.xlsx','-{}.xlsx'.format(fileindex))

				print('to create file: %s' % xlsx_file)

				wb = Workbook()
				sheet = wb.active
				
				sheet.append(headers)

			sheet.append(r)
			cnt_rows += 1

			if cnt_rows == max_num_of_rows:
				wb.save(xlsx_file)
				cnt_rows = 0 #reset
		
		if cnt_rows > 0:
			#some rows remaining
			wb.save(xlsx_file)



def create_multi_columns(data, basename, maxcol):
	
	if not data:
		data = []
		

	if isinstance(basename, basestring):
		#simple case

		res = []

		if len(data) < maxcol:
			#normalize
			for i in range(maxcol-len(data)):
				data.append('')

		for i in range(maxcol):
			res.append('{} {}'.format(basename, i+1))
			res.append(data[i])

		return res

	else:
		#complex case: each column is a set of sub-columns
		res = []

		if len(data) < maxcol:
			#normalize
			for i in range(maxcol-len(data)):
				fakevalues = ['' for j in range(len(basename))]

				data.append(fakevalues)

		for i in range(maxcol):
			values = data[i]

			j = 0
			for subbasename in basename:

				res.append('{} {}'.format(subbasename, i+1))
				res.append(values[j])

				j+=1

		return res	


def md5(text):
	return hashlib.md5(text).hexdigest()

def put_bin(path, data):	
	if not data:
		return False
	try:		
		f = codecs.open(path, 'wb')
		f.write(data)
		f.close()
		return True
	except Exception as e:
		logger.exception(e)
		return False

def put_file(path, data, encoding = 'utf-8'):
	#f = open(path, 'w')
	#convert backslash to forthslash
	path = path.replace('\\','/')
	

	f = codecs.open(path, 'w', encoding)
	f.write(data)
	f.close()

def get_file(path, encoding = 'utf-8'):	
	
	path = path.replace('\\','/')

	with codecs.open(path, encoding=encoding) as f: 
		data = f.read(); 
	return data	

def append_file(path, data, encoding='utf-8'):
	with codecs.open(path, 'a', encoding=encoding) as f: 		
		f.write(data)

	
def read_lines(path, removeempty = True, trim = True, encoding = 'utf-8'):
	
	lines = []
	with codecs.open(path, encoding=encoding) as f:
		for line in f.readlines():
			
			if removeempty and line.strip() == '':
				continue
			if trim:
				lines.append(line.strip())
			else:
				lines.append(line)

	return lines			
def read_lines_byrn(path, encoding = 'utf8'):
	with codecs.open(path, encoding=encoding) as f:
		buff = ''
		for line in f:			
			buff += line
			if line.endswith('\r\n'):
				yield buff
				buff = '' #clear buff
		if buff:
			#still got something left
			yield buff
																


def combine_dicts(basedict, dict2):
	newdict = copy.deepcopy(basedict)
	newdict.update(dict2)
	return newdict


def reg(s, reg):
	
	redata = parse_re_flags(reg)
	reg = redata['reg']
	flags = redata['flags'] or re.S
	m = re.search(reg, s, flags = flags)
	fields = re.findall('\?P<([\w\d]+)>', reg)
	
	res = DataObject()

	if m:
		for field, value in m.groupdict(default='').iteritems():
			# setattr(res, field, value)
			res[field] = value
	else:
		#no match, set default values
		for field in fields:
			res[field] = ''

	return res	
	
def subreg(s, reg, flags=re.S):
	m = re.search(reg, s, flags = flags)

	return DataItem( m.groups(0)[0] if m else '')

	
def sub(s, startstr, endstr):
	start = s.find(startstr) if startstr else 0
	if start == -1: return DataItem('') #not found
	start += len(startstr) # step over the startstr

	to = s.find(endstr, start) if endstr else len(s) #get to the end of string s if no end point provided
	if to == -1: return DataItem('') #not found
	return DataItem( s[start:to] )

def rr(pt, to, s, flags=re.S):
	
	return DataItem( re.sub(pt, to, s, flags = flags) )

def save_csv(path, record, sep=',', quote='"', escape = '"', write_header=True, always_quoted = True):
	
	#normalize the record to list

	if isinstance(record, OrderedDict):
	
		_record = []
		for key,value in record.items():
			_record += [key, value]

		record = _record


	elif isinstance(record, dict):
	
		_record = []
		for key in sorted(record.keys()):
			_record += [key, record[key]]

		record = _record	

	
	values = []
	keys = []
	
	for i, item in enumerate(record):
		if i % 2 == 0:
			#get key
			key = item.strip().replace(quote, escape + quote).replace('\r','')
			
			if always_quoted or sep in key:
				keys.append(quote + key + quote)
			else:
				keys.append(key)

		else:
			#get the value
			if item is None: item = DataItem()
			if not isinstance(item, DataItem): item = DataItem(item)

			value = item.trim().replace(quote, escape + quote).replace('\r','').replace('\u00A0',' ').trim().tostring()
			if always_quoted or sep in value:
				values.append(quote + value + quote)
			else:
				values.append(value)
					
				

	
	if not os.path.exists(path) and write_header:
		append_file(path, sep.join(keys)+'\r\n' + sep.join(values)+'\r\n')
	else:		
		append_file(path, sep.join(values)+'\r\n')	

def filename(path):
	path = DataItem(path).rr('\?.*?$')
	return path.subreg('/([^/\?\$]+\.[a-z]{2,4})$', re.I|re.S)

def file_ext(path):
	""" extract file extension from the path or url """
	path = DataItem(path).rr('\?.*?$').split('.')
	ext = path[-1].lower() if len(path)>1  else None

	return ext



def parse_address(full, two_address_lines = False):	

	full = DataItem(full).replace('\u00A0',' ').rr('\s+',' ').trim()
	
	#normalize the full address when full looks like: Some City, State zipcode
	if len(full.split(',')) == 2:
		full = '__nostreet123, ' + full

	full = DataItem(full if full else '').trim()
	

	zip = full.subreg('(?: |,)\s*(\d{4,5} ?- ?\d{3,4})$', re.I|re.S).tostring() or full.subreg('(?: |,)\s*(\d{9})$', re.I|re.S).tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$', re.I|re.S).tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$', re.I|re.S).tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$', re.I|re.S).tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$', re.I|re.S).tostring()

	if not zip:
		zip = full.subreg('(?: |,)\s*(\d{4,5})$', re.I|re.S)

	full = DataItem(full+'<end>').replace(zip+'<end>', '').trim().rr(',$','').trim()
	state = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(state+'<end>', '').trim().rr(',$','').trim()
	city = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(city+'<end>', '').trim().rr(',$','').trim()
	street = full.tostring().replace('__nostreet123', '')

	street1 = ''
	street2 = ''
	if ',' in street:
		street2 = subreg(street,',([^\,]+)$')
		street1 = subreg(street,'^(.*?),(?:[^\,]+)$')
	else:
		street2 = ''
		street1 = street
	if not two_address_lines:	
		address = {
			'address': street,
			'city': city,
			'state': state,
			'zipcode': zip

		}		
	else:
		address = {
			'address_line1': street1,
			'address_line2': street2,
			'city': city,
			'state': state,
			'zipcode': zip

		}	


	return address

def address(full_address):
	""" just for backward support """
	a = parse_address(full_address)

	ret = DataItem()
	ret.street = a['address']
	ret.city = a['city']
	ret.state = a['state']
	ret.zip = a['zipcode']

	return ret

def split_csv(path, maxlines):
	dir = os.path.dirname(os.path.abspath(path))
	_filename = filename(path)
	fno =1
	cnt=0
	headline = None
	for line in read_lines_byrn(path):		
		if headline is None:
			headline = line
			continue #don't treat this line as data line

		cnt += 1

		if cnt>maxlines:			
			fno += 1
			cnt = 1
		#add headline for new file	
		if cnt==1:
			append_file(os.path.join(dir, _filename.replace('.csv','-%s.csv'%fno)), headline)		

		#add data line	
		append_file(os.path.join(dir, _filename.replace('.csv','-%s.csv'%fno)), line)
def get_email(txt):
	
	email = subreg(txt, r'\b([A-Z0-9._%-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b', re.I|re.S)
	if '%' in email or 'email' in email.lower():
		email = DataItem('')

	return email	
		

def html_decode(encodedstr):
	parser = HTMLParser()
	return parser.unescape(encodedstr)
def parsecookies(cookiestr):
	cookiestr = cookiestr.replace('Cookie: ','')
	cookies = []
	for cookie in cookiestr.split('; '):
		cookie = DataItem(cookie).trim().reg('^(?P<name>[^=]+)=(?P<value>.*?)$');
		cookies.append((cookie.name, cookie.value,))
	return dict(cookies)		
def save_object(fullpath, obj):
	with open(fullpath,'wb') as f:
		pickle.dump(obj, f)
		
def load_object(fullpath):
	with open(fullpath,'rb') as f:
		return pickle.load(f)
def atoz():
	return [alpha for alpha in string.lowercase]
def AtoZ():
	return [alpha for alpha in string.uppercase]	
def urlencode(rawstr):
	rawstr = rawstr.encode('utf8')
	return DataItem( urllib.parse.quote_plus(rawstr) )
def urldecode(rawstr):
	return DataItem(urllib.parse.unquote(rawstr))	
def get_domain(url):
	urldata = urllib.parse.urlparse(url)
	return DataItem(urldata.netloc).rr('^[w\d]+\.','')
def get_emails(doc):
	doc = DataItem(doc)
	doc = doc.rr("\(at\)|\[at\]| \(at\) | \[at\] ", '@', flags=re.I|re.S)
	
	emails = re.compile(r'\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b', re.S|re.I).findall(doc)

	res = []
	for email in emails:
		if re.compile('(\.htm|\.html|\.jpg|\.jpeg|\.gif|\.png|\.pdf|\.php|\.aspx|\.tif|\.tiff|\.bmp)$', re.I).search(email):
			continue
		if email not in res:
			res.append(email)	
	return res		

def parse_name(fullname):
	"""
	todo: 
	
	- complete the SURFFIX_LIST constant
	- complete the REFIX_LIST constant

	"""

	from ._name import (SURFFIX_LIST, PREFIX_LIST)

	fullname = DataItem(fullname).rr('\s+',' ').trim()

	parts = fullname.split(' ')

	firstname = ''
	lastname = ''
	midname = ''
	surffix = ''
	prefix = ''



	surffix = parts[-1]
	if surffix.endswith('.'):
		
		surffix = '{}<end>'.format(surffix).replace('.<end>','').strip()


	if surffix in SURFFIX_LIST: 
		#a valid surfix
		
		del parts[-1]


	else:

		surffix = ''	

	prefix = parts[0]

	if prefix.endswith('.'):
		
		prefix = '{}<end>'.format(prefix).replace('.<end>','').strip()


	if prefix in PREFIX_LIST: 
		#a valid surfix
		
		del parts[0]



	else:

		prefix = ''		


	if len(parts) == 1:
		lastname = parts[0]

	elif len(parts)	== 2:
		firstname = parts[0]
		lastname = parts[1]
	elif len(parts) > 2:
		firstname = parts[0]
		lastname = parts[-1]		
		del parts[0]
		del parts[-1]
		midname = ' '.join(parts)

	return {
		'fullname': fullname,
		'prefix': prefix,
		'surffix': surffix,
		'firstname': firstname,
		'lastname': lastname,
		'midname': midname

	}	


def normalize_url(url):
	try:
		return str(url)
	except:
		try:
			return str( urllib.parse.quote(url.encode('utf8'), safe="%/:=&?~#+!$,;'@()*[]") )
		except:
			return str( urllib.parse.quote(url.encode('latin1'), safe="%/:=&?~#+!$,;'@()*[]") )
			
	
def rand_sort(input_list):
	items = []
	for item in input_list:
		_item = (random.randint(0, 10000), item)
		items.append(_item)
	
	items = sorted(items, key= lambda item: item[0])

	return [item[1] for item in items]
		

def start_threads(items, worker, cc=1, timeout=None, start_delay=1):
	
	logger = logging.getLogger(__name__)

	class Worker(threading.Thread):	
		def __init__(self, queue, func):
			threading.Thread.__init__(self)		
			self.queue = queue	
			self.func = func

		def run(self):
			try:
				while True:					
					item = self.queue.get(block=False) #get immediately or raise exception
					try:										
						self.func(item)
					except Exception as e:
						logger.exception('thread item error')
						
					finally:	
						self.queue.task_done()
			except Exception:			
				logger.debug('thread done')
				

	queue = Queue()
	for item in items:
		queue.put(item)
	#start workers		
	for i in range(cc):		
		t = Worker(queue = queue, func=worker)			
		t.setDaemon(True)
		
		time.sleep(random.uniform(0, start_delay) )	

		t.start()	
	if not timeout:	
		queue.join()	
	else:
		#join with timeout
		stop_time = time.time() + timeout
		while queue.unfinished_tasks and time.time() < stop_time:
			time.sleep(0.3)
	
	if queue.unfinished_tasks:
		#not all tasks done yet
		logger.warn('pending tasks in queue: %s', len(queue.unfinished_tasks))		


def to_json_string(js):
	return json.dumps(js, indent=4, sort_keys=True)

def read_csv(path, restype='list', encoding='utf8', line_sep='\r\n'):
	"""
	restype: list, dict
	"""
	i=-1
	fields = None
	lines = read_lines_byrn(path, encoding=encoding) if line_sep == '\r\n' else read_lines(path)
	for line in lines:
		i += 1
		r = [str(cell, encoding) for cell in next(csv.reader(io.StringIO(line.encode(encoding)))) ]

		if i == 0:
			fields = r
			if restype == 'list':
				yield r
			
			continue	

		if restype == 'list':
			yield r
		elif restype == 'dict':
			res = dict()
			for field in fields:
				res.update({field: r[fields.index(field)] })
			yield res
		
def csv_to_excel(csvfile, excelfile=None):
	from . import excellib
	if not excelfile:
		excelfile = DataItem(csvfile).rr('\.csv$','.xls', flags=re.I|re.S)	

	excellib.csvdatatoxls(excelfile,read_csv(csvfile))
def write_json(filepath, data):
	put_file(filepath, to_json_string(data))
def read_json(filepath):
	return json.loads(get_file(filepath))

def parse_log(filepath):
	logdata = get_file(filepath)
	warnings = len( re.compile('WARNING:').findall( logdata) )
	errors = len( re.compile('ERROR:').findall(logdata) )
	
	return {'warnings': warnings, 'errors': errors}
def parse_headers(headers_text):
	headers_text = headers_text.strip()
	headers = {}
	hs = re.compile(r'([^\n\:]+):([^\n]+)').findall(headers_text)
	for name, value in hs:
		headers[name.strip()] = value.strip()
	return headers

def parse_table(table_node, restype='dict', more_xpath=None, cols=None):
	""" 
		parse a html table node into list of dict or list

		@restyp: dict or list
		@more_xpath: to parse more detail within each td tag

	"""
	
	all_rows = table_node.q("thead/tr") + table_node.q("tbody/tr") + table_node.q("tr")
	rs = []
	for r in all_rows:
		if cols and r.q("th | td").len() != cols:
			continue
		rs.append(r)	


	if len(rs) == 0:
		
		return []
	

	headers = []
	
	col_index = 0
	#capture headers
	for td in rs[0].q("td | th"):
		col_index += 1
		header = td.nodevalue().trim()
		if header:
			header.col_index = col_index
			headers.append(header)
	# logger.info('headers: %s', headers)
	#capture data rows
	dataset = []
	for r in rs[1:]:
		datarow = [] if restype=='list' else {}
		for header in headers:
			
			td = r.node("td[%s]"%header.col_index)
			value = ''
			if 'website' in header.lower():
				value = td.x(".//a/@href") or td.nodevalue().trim()
			else:
				value = td.nodevalue().trim()	

			if more_xpath:
				value.more_data = td.x(more_xpath).trim()
				


			if restype == 'list':	

				datarow += [
				header, value
				]	
			else:
				datarow[header] = value

		dataset.append(datarow)

	return dataset						

def list_to_dict(l):
	"""
	convert a list of key,value pair into dict """
	res = {}
	for i in range(0, len(l)):
		if i % 2 == 0:
			res[l[i]] = l[i+1]

	return res		

def parse_form_data(form_data_text, custom_params={}):
	"""
	
	@params: Query String Parameters, copied from Google Chrome's Network in this format:
	
	param1: some value
	param2: some more value
	.....
	
	@custom_params: to override the copied values

	@return:
		a encoded-string, ready to make http request

	"""
	
	listofparams = []
	for line in form_data_text.strip().split('\n'):
		line = line.strip()
		if not line:
			#empty line
			continue
		if line.startswith('#'):
			#commented param
			continue
		line = DataItem(line)
			
		name =  line.sub('',':')
		value =  line.subreg('^[^\:]+:(.*?)$')

		if name in custom_params:
			value = custom_params[name]
			if not isinstance(value, basestring):
				value = str(value)

		listofparams.append(
			'%s=%s' % (name, urlencode(value.encode('utf8')))
			)		

	return '&'.join(listofparams)



class DataItem(str):

	def __init__(self, data=''):
		
		self.data = data or ''
	
	
	def __repr__(self):
		
		return self.data	

	def __str__(self):
		
		return self.data

	
	def __unicode__(self):

		return self.data


	def tostring(self):
		return self.data						

	def replace(self, old, new=''):
		return DataItem(self.data.replace(old, new))

	def rr(self, old, new='', flags=re.S):
		return DataItem(rr(old, new, self.data, flags))
		
	def sub(self, startstr, endstr):
		return  DataItem(sub(self.data, startstr, endstr))
	
	def substr(self, startstr, endstr):
		return self.sub(startstr, endstr)
		
	def subreg(self, reg, flags=re.S):
		return DataItem(subreg(self.data, reg, flags=flags))
		
	def trim(self):
		return DataItem(self.data.strip())
	def strip(self):
		return self.trim()

	def urlencode(self):
		return DataItem(urllib.parse.quote_plus(self.data))
	def urldecode(self):
		return DataItem(urllib.parse.unquote(self.data))	
	
	def html_decode(self):
		return DataItem(html_decode(self.data))

	def len(self):
		return len(self.data)


if __name__ == '__main__':

	print(parse_address('2309 Foothill Blvd, La Canada Flintridge, CA 91011'))
