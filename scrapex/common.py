import hashlib, os, copy, codecs, re,urllib, urlparse, json, string, threading, StringIO, csv, logging, pickle, random,time
from Queue import Queue
from HTMLParser import HTMLParser

logger = logging.getLogger()

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
	except Exception, e:
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
		buff = u''
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
def parse_re_flags(reg):
	#parse flags
	_flags = []
	flags = None
	
	options = re.search('--[a-z]+$', reg, flags= re.S|re.I)
	
	if options:		
		options = options.group().replace('--','')
		
		reg = re.sub(r'--[a-z]+$', '', reg) #remove options part from reg string

		for option in options.lower():
			if option == 'i': _flags.append(re.I)
			elif option == 's': _flags.append(re.S)
			elif option == 'm': _flags.append(re.M)
			elif option == 'u': _flags.append(re.U)

		for flag in _flags:
			flags = flags | flag if flags is not None else flag	

	return dict(reg = reg, flags = flags)		
	
def subreg(s, reg):
	
	redata = parse_re_flags(reg)
	reg = redata['reg']
	flags = redata['flags'] or re.S
	m = re.search(reg, s, flags = flags)
	return DataItem( m.groups(0)[0] if m else '')

def reg(s, reg):
	
	redata = parse_re_flags(reg)
	reg = redata['reg']
	flags = redata['flags'] or re.S
	m = re.search(reg, s, flags = flags)
	fields = re.findall('\?P<([\w\d]+)>', reg)
	
	res = DataObject()

	if m:
		for field, value in m.groupdict(default='').iteritems():
			setattr(res, field, value)
	else:
		#no match, set default values
		for field in fields:
			setattr(res, field, '')	

	return res	


	
def sub(s, startstr, endstr):
	start = s.find(startstr) if startstr else 0
	if start == -1: return DataItem('') #not found
	start += len(startstr) # step over the startstr

	to = s.find(endstr, start) if endstr else len(s) #get to the end of string s if no end point provided
	if to == -1: return DataItem('') #not found
	return DataItem( s[start:to] )
def rr(pt, to, s):
	redata = parse_re_flags(pt)
	reg = redata['reg']
	flags = redata['flags'] or re.S	
	return DataItem( re.sub(reg, to, s, flags = flags) )

def save_csv(path, record, sep=',', quote='"', escape = '"', write_header=True):

	#normalize the record to list
	if isinstance(record, dict):
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
			keys.append(quote + key + quote)
		else:
			#get the value
			if item is None: item = DataItem()
			if not isinstance(item, DataItem): item = DataItem(item)

			value = item.trim().replace(quote, escape + quote).replace('\r','').replace(u'\u00A0',' ').trim().tostring()
			values.append(quote + value + quote)
				

	
	if not os.path.exists(path) and write_header:
		append_file(path, sep.join(keys)+'\r\n' + sep.join(values)+'\r\n')
	else:		
		append_file(path, sep.join(values)+'\r\n')	

def file_name(path):
	path = DataItem(path).rr('\?.*?$')
	return path.subreg('/([^/\?\$]+\.[a-z]{2,4})$--is')

def file_ext(path):
	""" extract file extension from the path or url """
	path = DataItem(path).rr('\?.*?$').split('.')
	ext = path[-1].lower() if len(path)>1  else None

	return ext



def address(full, two_lines=False):	

	full = DataItem(full).replace(u'\u00A0',' ').rr('\s+',' ').trim()
	bkfull = full

	#normalize the full address when full looks like: Some City, State zipcode
	if len(full.split(',')) == 2:
		full = '__nostreet123, ' + full

	full = DataItem(full if full else '').trim()
	

	zip = full.subreg('(?: |,)\s*(\d{4,5} ?- ?\d{3,4})$--is').tostring() or full.subreg('(?: |,)\s*(\d{9})$--is').tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$--is').tostring()

	if not zip:
		zip = full.subreg('(?: |,)\s*(\d{4,5})$--is')

	full = DataItem(full+'<end>').replace(zip+'<end>', '').trim().rr(',$','').trim()
	state = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(state+'<end>', '').trim().rr(',$','').trim()
	city = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(city+'<end>', '').trim().rr(',$','').trim()
	street = full.tostring().replace('__nostreet123', '')

	street2 = ''
	if two_lines and ',' in street:
		street2 = subreg(street,',([^\,]+)$')
		street = subreg(street,'^(.*?),(?:[^\,]+)$')


	return Address(street = street, street2=street2, city= city, state = state, zip = zip, full = bkfull)		




def split_csv(path, maxlines):
	dir = os.path.join(path,'..')
	_file_name = file_name(path)
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
			append_file(os.path.join(dir, _file_name.replace('.csv','-%s.csv'%fno)), headline)		

		#add data line	
		append_file(os.path.join(dir, _file_name.replace('.csv','-%s.csv'%fno)), line)
def get_email(txt):
	return subreg(txt, r'\b([A-Z0-9._%-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b--is')

def toml(des):
	
	#normalize the input
	des = DataItem(des).rr(r'\bfl\.?--is','').rr('\s+',' ')
	#the ml already in the des
	if des.subreg('\\b([\d\.]+)\s*ml\\b--is'):
		return des.subreg('\\b([\d\.]+)\s*ml\\b--is') + ' ml'



	ms = re.findall(r'(?:[1-9]{1}[0-9]{0,}(?:\.[0-9]{0,3})?|0(?:\.[0-9]{0,3})?|\.[0-9]{1,3}) ?oz',des, flags = re.I|re.S)

	for m in ms:
		try:
			bk_m = m			
			m = DataItem(m).rr('oz--is','').rr('fl--is','').trim()
			value = float(m)
			size_ml = value * 29.5735296875
			if size_ml > 5:
				size_ml =  round(size_ml, 0)
			else:
				size_ml = round(size_ml, 2)

			newsize = ('%d ml' % size_ml) if size_ml>5 else ('%s ml' % size_ml)
			des = des.replace(bk_m, newsize)
		except Exception:
			return des

	return des.subreg('([\d\.]+)\s*ml--is')	+ ' ml' if des.subreg('([\d\.]+)\s*ml--is') else des
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
	return DataItem( urllib.quote_plus(rawstr) )
def urldecode(rawstr):
	return DataItem(urllib.unquote(rawstr))	
def get_domain(url):
	urldata = urlparse.urlparse(url)
	return DataItem(urldata.netloc).rr('^[w\d]+\.','')
def get_emails(doc):
	doc = DataItem(doc)
	doc = doc.rr("\(at\)|\[at\]| \(at\) | \[at\] --is", '@')
	
	emails = re.compile(r'\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b', re.S|re.I).findall(doc)

	res = []
	for email in emails:
		if re.compile('(\.htm|\.html|\.jpg|\.jpeg|\.gif|\.png|\.pdf|\.php|\.aspx|\.tif|\.tiff|\.bmp)$', re.I).search(email):
			continue
		if email not in res:
			res.append(email)	
	return res		

def parse_name(full):
	
	item = DataItem(full).trim()
	first = item.subreg('^(.*?)\s+(?:[^\s]+)$')
	last = item.subreg('^(?:.*?)\s+([^\s]+)$') or item
	return DataObject(first=first, last=last, full=full)

def readconfig(path):
	configstr = DataItem(get_file(path) + '\n')
	configstr = configstr.rr(r'^\s*\#.*?$--m','')
	
	config = DataObject()
	names = re.compile(r'^\s*[\w]{5,}\:', re.M).findall(configstr)
	for name in names:
		#config.update({name.replace(':','').strip() : configstr.sub(name,'\n').trim() })
		config.set( name.replace(':','').strip(), configstr.sub(name,'\n').trim() )
	
	return config
def normalize_url(url):
	try:
		return str(url)
	except:
		try:
			return str( urllib.quote(url.encode('utf8'), safe="%/:=&?~#+!$,;'@()*[]") )
		except:
			return str( urllib.quote(url.encode('latin1'), safe="%/:=&?~#+!$,;'@()*[]") )
			
	
def rand_sort(input_list):
	items = []
	for item in input_list:
		_item = (random.randint(0, 10000), item)
		items.append(_item)
	
	items = sorted(items, key= lambda item: item[0])

	return [item[1] for item in items]
		

def start_threads(items, worker, cc=1, timeout=None):
	
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
					except Exception, e:
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
	restype: list, dict, DataObject
	"""
	i=-1
	fields = None
	lines = read_lines_byrn(path, encoding=encoding) if line_sep == '\r\n' else read_lines(path)
	for line in lines:
		i += 1
		r = [unicode(cell, encoding) for cell in csv.reader(StringIO.StringIO(line.encode(encoding))).next() ]

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
		else:			
			res = DataObject()
			for field in fields:
				setattr(res, field, r[fields.index(field)] )
			yield res
def csv_to_excel(csvfile, excelfile=None):
	import excellib
	if not excelfile:
		excelfile = DataItem(csvfile).rr('\.csv$--is','.xls')	

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


	
class DataItem(unicode):

	def __init__(self, data=u''):
		
		if data is None: data = ''

		self.data = unicode(data)
	
	
	def __repr__(self):
		return self.data	

	def __str__(self):
		return self.data

	def tostring(self):
		return self.data						

	def replace(self, old, new=''):
		return DataItem(self.data.replace(old, new))		

	def rr(self, old, new=''):
		return DataItem(rr(old, new, self.data))
		
	def sub(self, startstr, endstr):
		return  DataItem(sub(self.data, startstr, endstr))
		
	def subreg(self, reg):
		return DataItem(subreg(self.data, reg))
		
	def trim(self):
		return DataItem(self.data.strip())
	def urlencode(self):
		return DataItem(urllib.quote_plus(self.data))
	def urldecode(self):
		return DataItem(urllib.unquote(self.data))	
	def reg(self, regpattern):
		return reg(self.data, regpattern)
	def html_decode(self):
		return DataItem(html_decode(self.data))

	def len(self):
		return len(self.data)
	def print_(self):
		print self.encode('utf8')
	def strip_links(self):
		return self.rr('<a [^<>].*?>(.*?)</a>--is', r'\1')

class Address(object):		
	def __init__(self, street='', street2='', city='', state='', zip ='', country = '', full=''):			
		self.street= street
		self.street2 = street2
		self.city = city
		self.state = state
		self.zip = zip
		self.country = country,
		self.full = full
	def __str__(self):
		return unicode('street: %s, street2: %s, city: %s, state: %s, zip: %s, country: %s' % (self.street, self.street2, self.city, self.state, self.zip, self.country))				
		
class DataObject(object):
	def __init__(self, **data):
		for key, value in data.iteritems():
			setattr(self,key,value)

	def set(self, key, value):
		setattr(self,key,value)
		return self
	def __setitem__(self, key, value):
		self.set(key, value)
		return self
	def __getitem__(self, key):
		if hasattr(self, key):
			return getattr(self, key)
		else:
			raise Exception('DataObject key error: %s', key)
				

	def from_list(self, arr, trim=True):
		i=0
		while i< len(arr) - 1:
			value = arr[i+1]
			if trim and isinstance(value, basestring):				
				value = value.strip()

			self.set(arr[i], value)

			i+=2

		return self
	def to_list(self, headers = []):
		if not headers:
			for att in dir(self):
				value = getattr(self, att)
				if '__' not in att and not hasattr(value, '__call__'):
					headers.append(att)
		res = []
		for att in headers:
			res += [att, getattr(self, att)]	
		return res	


	def __str__(self):
		data = []
		for att in dir(self):
			value = getattr(self, att)
			if '__' not in att and not hasattr(value, '__call__'):
				data.append(u'{0}: {1}'.format(att, value))
		
		return '\n'.join(data)	


class MyDict(object):
	def __init__(self, **data):
		self.data = data
	def update(self, dict={}, **data):
		self.data.update(data)
		self.data.update(dict)
		return self
	def from_post_string(self, post):
		self.update(dict(urlparse.parse_qsl(post)))
		return self
	def update_from_doc(self, doc,keys=[], exceptkeys=[]):
		for name, value in doc.form_data().iteritems():
			if name in exceptkeys:
				continue
			if keys and name not in keys:
				continue	
			if name not in self.data.keys():
				if keys and name in keys:
					pass
				else:
					continue
			
			self.update({name:value})
		return self		

	def dict(self):
		return self.data	

	def __str__(self):
		print '__str__'
		return str(self.data)


class UList(list):
	def __init__(self, initlist=[]):
			
		for item in initlist:
			self.append(item)

	def append(self, item):
		try:
		 	self.index(item)
		except:
			#not found, so add to		
			super(UList, self).append(item)
		return self	
	def join(self, sep=u', '):
		return sep.join(self)

if __name__ == '__main__':

	print	parse_log('log.txt')
