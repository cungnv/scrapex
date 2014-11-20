import sys, urlparse, requests, time, zlib, json, re
from node import Node
from cache import Cache
import common, agent


ERROR_CONNECTION = 1 # cannot connect to the server
ERROR_SERVER = 2 #internal server error
ERROR_NOT_FOUND = 3 # the url is not found (404)
ERROR_TIMEOUT = 4 # read timeouted
ERROR_DENIED = 5 # request denied by server
ERROR_INVALID_HTML = 6
ERROR_MISC = 7 # the rest
errordesc = {
	ERROR_CONNECTION: 'cannot connect to the server',
	ERROR_SERVER: 'internal server error',
	ERROR_NOT_FOUND: 'url not found',
	ERROR_TIMEOUT: 'timeout',
	ERROR_DENIED: 'request denied/blocked',
	ERROR_INVALID_HTML: 'invalid html',
	ERROR_MISC: 'Mics.'

}

class MyStr():
	pass
class Status():
	""" the object returned by http.open function always contains an instance of Status class"""
	def __init__(self, code, finalurl, error=None):
		self.code = code
		self.finalurl = finalurl
		self.error = error

	def __str__(self):
		print '__str__'
		return str("code: %s, error: %s (%s), finalurl: %s" % (self.code, self.error, errordesc[self.error] ,self.finalurl))

	
class DOM(Node):
	def __init__(self, status, url='', html='<html></html>', passdata= {}, htmlclean=None):		
		if htmlclean:
			html = htmlclean(html)

		Node.__init__(self, html)
		self.url = common.DataItem( url )
		self.passdata = passdata if passdata else {}
		self.status = status
		

		
		
		#resolve relative urls
		baseurl = self.x("//base/@href").tostring()
		if not baseurl:
			baseurl = self.url
		
		for n in self.q('//a[@href and not(contains(@href, "javascript")) and not(contains(@href, "#")) and not(contains(@href, "mailto:"))]'):					
			if n.href().trim() == '': continue
			n.set('href', urlparse.urljoin(baseurl, n.get('href').tostring()))

		for n in self.q('//iframe[@src]'):					
			if n.src().trim() == '': continue
			n.set('src', urlparse.urljoin(baseurl, n.src()))
	


		for n in self.q('//form[@action]'):					
			n.set('action', urlparse.urljoin(baseurl, n.get('action').tostring()))	
		for n in self.q('//img[@src]'):					
			n.set('src', urlparse.urljoin(baseurl, n.get('src').tostring()))		
	def formdata(self):
		data = dict()
		for node in self.q("//input[@name and @value]"):
			data.update(dict( ( (node.name(), node.value(),), ) ))

		return data	
	def aspx_vs(self):
		return self.x("//input[@id='__VIEWSTATE']/@value").urlencode() or self.html().sub('__VIEWSTATE|','|').urlencode()
	def aspx_ev(self):
		return self.x("//input[@id='__EVENTVALIDATION']/@value").urlencode() or self.html().sub('__EVENTVALIDATION|','|').urlencode()
	def aspx_prepage(self):
		return self.x("//input[@id='__PREVIOUSPAGE']/@value").urlencode() or self.html().sub('__PREVIOUSPAGE|','|').urlencode()	




class Request(object):	
	def __init__(self, url, post = None, passdata={}, **options):		
		self.url = url	
		self.post = post
		self.options = options
		if passdata:
			self.options.update(dict(passdata=passdata))
		

	def get(self, name, default = None):
		return self.options.get(name, default)
	def set(self, name, value):
		return self.options.set(name, value)	

	def update(self, dict2):
		self.options.update(dict2)
		return self



def open(req):

	meta_seperator = '=======META======'
	
	#normalise the post
	if req.post and isinstance(req.post, common.MyDict):
		req.post = req.post.dict()
				
	cache = req.get('cache') if isinstance(req.get('cache'), Cache) else None
	
	#try read from cache first
	if cache and cache.exists(url = req.url, post = req.post, filename = req.get('filename')):
		cachedata = cache.read(url = req.url, post = req.post, filename = req.get('filename')).split(meta_seperator)
		
		cachedhtml = None
		status = Status(code=200, finalurl=None, error=None)
		if len(cachedata)==2:
			cachedhtml = cachedata[1]
			meta = json.loads( cachedata[0] )
			#reload status
			status = Status(code= meta['status']['code'], finalurl = meta['status']['finalurl'], error = meta['status'].get('error', None) )
		else:
			#no meta data
			cachedhtml = cachedata[0]


		if req.get('bin'):
			data = MyStr(cachedhtml)
			data.status = status
			return data
		else:

			return DOM(url=req.url, status = status , passdata = req.get('passdata'), html= cachedhtml, htmlclean = req.get('htmlclean'))


	client = req.get('client') if req.get('client') else requests


	
	#default headers
	headers = {
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"User-Agent": agent.firefox,
		"Accept-Language": "en-us,en;q=0.5",
		"Accept-Encoding": "gzip, deflate",			
		"Connection": "close" #turn off keep-alive
	}
	if req.post:
		headers.update({"Content-Type": "application/x-www-form-urlencoded"})
		
	#update user-passed in headers
	headers.update(req.get('headers', {})) 


	proxy = req.get('proxy', None)	
	proxyauth = req.get('proxyauth', None)
	if proxy:
		if proxyauth:
			proxies = {
				'http': 'http://{0}@{1}'.format(proxyauth, proxy),
				'https': 'http://{0}@{1}'.format(proxyauth, proxy)
			}
		else:
			proxies = {
				'http': 'http://{0}'.format(proxy),
				'https': 'http://{0}'.format(proxy)
			}
	else:
		proxies = None

	tries = req.get('retries', 0)	
	
	statuscode = None
	finalurl = None
	try:
		time.sleep(req.get('delay', 0.001))	
		r = None	
		if req.post:
			r = client.post(req.url, data = req.post, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream=True, cookies= req.get('cookies', None))
		else:	
			r = client.get(req.url, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream = True, cookies= req.get('cookies', None))
		
		if r.status_code != 200:
			statuscode = r.status_code
			finalurl = r.url

			raise Exception('Invalid status code: %s' % r.status_code)
		if 'gzip' in r.headers.get('content-encoding', ''):
			bytes = zlib.decompress(r.raw.read(), 16+zlib.MAX_WBITS)	

		elif 'deflate' in r.headers.get('content-encoding', ''):

			bytes = zlib.decompressobj(-zlib.MAX_WBITS).decompress(r.raw.read())	
		
		else:
			bytes = r.raw.read()	
					
		if req.get('bin') is True:
			#download binary file			
			if cache:
				meta = {
					'url': req.url,
					'status': {
						'code': r.status_code,
						'finalurl': r.url,
						'error': None
					}
				}				
				cache.write(url= req.url, post=req.post, filename = req.get('filename'), data = ''.join([json.dumps(meta), meta_seperator, bytes]) ) # in utf8 format
			mystr = MyStr(bytes)	
			mystr.status = Status(code=r.status_code, finalurl = r.url)
			return mystr

		html = bytes.decode(req.get('encoding', r.encoding), 'ignore')

		#verify data
		if req.get('contain') and req.get('contain') not in html:
			raise Exception("invalid html, not contain: {0}".format(req.get('contain')))
		verify = req.get('verify')
		
		if verify and (not verify(html)):
			raise Exception("invalid html")
		
		#write html to cache
		if cache:
			meta = {
				'url': req.url,
				'status': {
					'code': r.status_code,
					'finalurl': r.url,
					'error': None
				}
			}

			cache.write(url= req.url, post=req.post, filename = req.get('filename'), data = ''.join( [json.dumps(meta), meta_seperator, html.encode('utf8') ] ).decode('utf8') )
		
		return DOM(html=html, url = req.url, passdata = req.get('passdata'), htmlclean = req.get('htmlclean'), status= Status(code=r.status_code, finalurl = r.url) )		

	except Exception, e:
		message = str(e.message)
		print message
		if tries > 0:
			#try to open the request one again	
			req.update({'retries': tries - 1})
			return open(req)
		
		error = None
		if 'errno 11001' in message.lower():
			error = ERROR_CONNECTION
		elif statuscode in [404]:
			error = ERROR_NOT_FOUND
		elif statuscode in [403]:
			error = ERROR_DENIED
		elif statuscode in [500]:
			error = ERROR_SERVER
		elif 'timeout' in message.lower():
			error = ERROR_TIMEOUT
		elif 'invalid html' in message.lower():
			error = ERROR_INVALID_HTML	
		else:
			error = ERROR_MISC


		status = Status(code = statuscode, finalurl = finalurl or req.url, error = error )

		if req.get('bin') is True:
			mystr = MyStr()
			mystr.status = status
			return mystr

		else:		
			return DOM(url=req.url, passdata = req.get('passdata'), status = status)

def getredirecturl(url):
	res = requests.head(url=url, allow_redirects = False)
	return res.headers.get('location') or res.headers.get('Location', '')

