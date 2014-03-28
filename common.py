import hashlib, os, copy, codecs, re,urllib, urlparse, json, string
from HTMLParser import HTMLParser
import pickle


def md5(text):
	return hashlib.md5(text).hexdigest()
def putbin(path, data):	
	if not data: return False
	try:		
		f = codecs.open(path, 'wb')
		f.write(data)
		f.close()
		return True
	except Exception, e:
		print e	
		return False

def putfile(path, data, encoding = 'utf-8'):
	#f = open(path, 'w')
	
	f = codecs.open(path, 'w', encoding)
	f.write(data)
	f.close()

def getfile(path, encoding = 'utf-8'):	
	with codecs.open(path, encoding=encoding) as f: 
		data = f.read(); 
	return data	

def appendfile(path, data, encoding='utf-8'):
	with codecs.open(path, 'a', encoding=encoding) as f: 		
		f.write(data)

	
def readlines(path, removeempty = True, trim = True, encoding = 'utf-8'):
	
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
def readlinesbyrn(path, encoding = 'utf-8'):
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
																


def combinedicts(basedict, dict2):
	newdict = copy.deepcopy(basedict)
	newdict.update(dict2)
	return newdict
def parsereflags(reg):
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
		for flag in _flags:
			flags = flags | flag if flags is not None else flag	

	return dict(reg = reg, flags = flags)		
	
def subreg(s, reg):
	
	redata = parsereflags(reg)
	reg = redata['reg']
	flags = redata['flags'] or re.S
	m = re.search(reg, s, flags = flags)
	return DataItem( m.groups(0)[0] if m else '')

def reg(s, reg):
	
	redata = parsereflags(reg)
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
	if start == -1: return '' #not found
	start += len(startstr) # step over the startstr

	to = s.find(endstr, start)
	if to == -1: return '' #not found
	return DataItem( s[start:to] )
def rr(pt, to, s):
	redata = parsereflags(pt)
	reg = redata['reg']
	flags = redata['flags'] or re.S	
	return DataItem( re.sub(reg, to, s, flags = flags) )

def savecsv(path, record, sep=',', quote='"', escape = '"'):		
	values = []
	keys = []
	# for k in record:		
	# 	value = record[k].trim().replace(quote, escape + quote).replace('r','')
	# 	key = k.strip().replace(quote, escape + quote).replace('r','')
	# 	keys.append(quote + key + quote)
	# 	values.append(quote + value + quote)

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
				

	# if not os.path.exists(path):
	# 	appendfile(path, sep.join(keys)+'\r\n')

	# appendfile(path, sep.join(values)+'\r\n')	

	if not os.path.exists(path):
		appendfile(path, sep.join(keys)+'\r\n' + sep.join(values)+'\r\n')
	else:		
		appendfile(path, sep.join(values)+'\r\n')	

def filename(path):
	return subreg(path, '/([^/\?\$]+\.[a-z]{2,4})$--is')

		

def address(full, twolines=False):	

	full = DataItem(full).replace(u'\u00A0',' ').rr('\s+',' ').trim()
	bkfull = full

	#normalize the full address when full looks like: Some City, State zipcode
	if len(full.split(',')) == 2:
		full = '__nostreet123, ' + full

	full = DataItem(full if full else '').trim()
	

	zip = full.subreg('(?: |,)\s*(\d{4,5} ?- ?\d{3,4})$--is').tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{1,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*(\d[a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$--is').tostring() or full.subreg('(?: |,)\s*([a-z][a-z\d]{1,3}[\s\-]{0,2}[a-z\d]{1,3})$--is').tostring()

	if not zip:
		zip = full.subreg('(?: |,)\s*(\d{4,5})$--is')

	full = DataItem(full+'<end>').replace(zip+'<end>', '').trim().rr(',$','').trim()
	state = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(state+'<end>', '').trim().rr(',$','').trim()
	city = full.subreg(',\s*([^\d\,#]{2,})$').tostring()
	full = DataItem(full+'<end>').replace(city+'<end>', '').trim().rr(',$','').trim()
	street = full.tostring().replace('__nostreet123', '')

	street2 = ''
	if twolines and ',' in street:
		street2 = subreg(street,',([^\,]+)$')
		street = subreg(street,'^(.*?),(?:[^\,]+)$')


	return Address(street = street, street2=street2, city= city, state = state, zip = zip, full = bkfull)		




def splitcsv(path, maxlines):
	dir = os.path.join(path,'..')
	_filename = filename(path)
	fno =1
	cnt=0
	headline = None
	for line in readlinesbyrn(path):		
		if headline is None:
			headline = line
			continue #don't treat this line as data line

		cnt += 1

		if cnt>maxlines:			
			fno += 1
			cnt = 1
		#add headline for new file	
		if cnt==1:
			appendfile(os.path.join(dir, _filename.replace('.csv','-%s.csv'%fno)), headline)		

		#add data line	
		appendfile(os.path.join(dir, _filename.replace('.csv','-%s.csv'%fno)), line)
def getemail(txt):
	return subreg(txt, r'\b([A-Z0-9._%-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b--is')

def toml(des):
	
	#normalize the input
	des = DataItem(des).rr(r'\bfl\.?--is','').rr('\s+',' ')
	ms = re.findall(r'(?:[1-9]{1}[0-9]{0,}(?:\.[0-9]{0,3})?|0(?:\.[0-9]{0,3})?|\.[0-9]{1,3}) ?oz',des, flags = re.I|re.S)

	for m in ms:
		try:
			bk_m = m
			print m
			m = DataItem(m).rr('oz--is','').rr('fl--is','').trim()

			value = float(m)
			size_ml = round(value * 29.5735296875, 0) # Convert.ToInt32(Math.Round((29.5735296875) * value, 0));
			newsize = '%d ml' % size_ml
			des = des.replace(bk_m, newsize)
		except Exception:
			return des

	return des.subreg('([\d\.]+)\s*ml--is')	+ ' ml' if des.subreg('([\d\.]+)\s*ml--is') else des
def htmldecode(encodedstr):
	parser = HTMLParser()
	return parser.unescape(encodedstr)
def parsecookies(cookiestr):
	cookiestr = cookiestr.replace('Cookie: ','')
	cookies = []
	for cookie in cookiestr.split('; '):
		cookie = DataItem(cookie).trim().reg('^(?P<name>[^=]+)=(?P<value>.*?)$');
		cookies.append((cookie.name, cookie.value,))
	return dict(cookies)		
def saveobject(fullpath, obj):
	with open(fullpath,'wb') as f:
		pickle.dump(obj, f)
		
def loadobject(fullpath):
	with open(fullpath,'rb') as f:
		return pickle.load(f)
def atoz():
	return [alpha for alpha in string.lowercase]
def AtoZ():
	return [alpha for alpha in string.uppercase]	
def urlencode(rawstr):
	return DataItem( urllib.quote_plus(rawstr) )
def getdomain(url):
	urldata = urlparse.urlparse(url)
	return DataItem(urldata.netloc).rr('^[w\d]+\.','')
def getemails(doc):
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

def parsename(full):
	
	item = DataItem(full).trim()
	first = item.subreg('^(.*?)\s+(?:[^\s]+)$')
	last = item.subreg('^(?:.*?)\s+([^\s]+)$') or item
	return DataObject(first=first, last=last, full=full)

def readconfig(path):
	configstr = common.DataItem(common.getfile(path) + '\n')
	configstr = configstr.rr(r'^\s*\#.*?$--m','')
	
	config = DataObject()
	names = re.compile(r'^\s*[\w]{5,}\:', re.M).findall(configstr)
	for name in names:
		#config.update({name.replace(':','').strip() : configstr.sub(name,'\n').trim() })
		config.set( name.replace(':','').strip(), configstr.sub(name,'\n').trim() )
	
	return config

	
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

	def rr(self, old, new):
		return DataItem(rr(old, new, self.data))
		
	def sub(self, startstr, endstr):
		return  DataItem(sub(self.data, startstr, endstr))
		
	def subreg(self, reg):
		return DataItem(subreg(self.data, reg))
		
	def trim(self):
		return DataItem(self.data.strip())
	def urlencode(self):
		return DataItem(urllib.quote_plus(self.data))
	def reg(self, regpattern):
		return reg(self.data, regpattern)
	def htmldecode(self):
		return DataItem(htmldecode(self.data))

	def len(self):
		return len(self.data)


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
	def fromlist(self, arr, trim=True):
		i=0
		while i< len(arr) - 1:
			value = arr[i+1]
			if trim and isinstance(value, basestring):				
				value = value.strip()

			self.set(arr[i], value)

			i+=2

		return self
	def __str__(self):
		data = []
		for att in dir(self):
			value = getattr(self, att)
			if '__' not in att and not hasattr(value, '__call__'):
				data.append(u'{0}: {1}'.format(att, value))
		return '{<DataObject> ' + ', '.join(data)	+ ' }'	


class MyDict(object):
	def __init__(self, **data):
		self.data = data
	def update(self, dict={}, **data):
		self.data.update(data)
		self.data.update(dict)
		return self
	def frompoststring(self, post):
		self.update(dict(urlparse.parse_qsl(post)))
		return self
	def dict(self):
		return self.data	

	def __str__(self):
		print '__str__'
		return str(self.data)


		