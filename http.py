import urlparse, requests, time, zlib
from node import Node
from cache import Cache
import common

def open(req, errorhandler = None):
	#fix the url
	# if ' ' in req.url:
	# 	req.url = req.url.replace(' ','+')
	errorhandler = req.get('errorhandler', None) #temp

	#normalise the post
	if req.post and isinstance(req.post, common.MyDict):
		req.post = req.post.dict()
				
	cache = req.get('cache') if isinstance(req.get('cache'), Cache) else None
	
	#try read from cache first
	if cache and cache.exists(url = req.url, post = req.post, filename = req.get('filename')):
		if req.get('bin'):
			return cache.read(url = req.url, post = req.post, filename = req.get('filename'))

		return DOM(url=req.url, passdata = req.get('passdata'), html=cache.read(url = req.url, post = req.post, filename = req.get('filename')), htmlclean = req.get('htmlclean'))


	client = req.get('client') if req.get('client') else requests


	
	#default headers
	headers = {
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2",
		"Accept-Language": "en-us,en;q=0.5",
		"Accept-Encoding": "gzip, deflate",	
			
		"Connection": "close"
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
	
	try:
		time.sleep(req.get('delay', 0.001))	
		r = None
		if req.post:
			r = client.post(req.url, data = req.post, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream=True, cookies= req.get('cookies', None))
		else:	
			r = client.get(req.url, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream = True, cookies= req.get('cookies', None))
		
		if r.status_code != 200:
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
				cache.write(url= req.url, post=req.post, filename = req.get('filename'), data = bytes) # in utf8 format

			return bytes

		html = bytes.decode(req.get('encoding', r.encoding), 'ignore')

		#verify data
		if req.get('contain') and req.get('contain') not in html:
			raise Exception("html not contain: {0}".format(req.get('contain')))
		verify = req.get('verify')
		
		if verify and (not verify(html)):
			raise Exception("html valid")
		
		#write html to cache
		if cache:
			cache.write(url= req.url, post=req.post, filename = req.get('filename'), data = html) # in utf8 format
		
		return DOM(html=html, url = req.url, passdata = req.get('passdata'), htmlclean = req.get('htmlclean'))		

	except Exception, e:		
		if tries > 0:
			#try to open the request one again	
			req.update({'retries': tries - 1})
			return open(req, errorhandler)

		if errorhandler:
			errorhandler(err = e, req = req, res = r)
		elif req.get('debug', True):
			print e, 'url: ', req.url
				
		if req.get('bin') is True:
			return None
		else:		
			return DOM(url=req.url, passdata = req.get('passdata'), statuscode = r.status_code if r else -1, ok=False)

def getredirecturl(url):
	res = requests.head(url=url, allow_redirects = False)
	return res.headers.get('location') or res.headers.get('Location', '')

class DOM(Node):
	def __init__(self, url='', html='<html></html>', passdata= {}, statuscode=200, htmlclean=None, ok=True):		
		if htmlclean:
			html = htmlclean(html)

		Node.__init__(self, html)
		self.url = common.DataItem( url )
		self.passdata = passdata if passdata else {}
		self.statuscode = statuscode
		self.ok = ok

		
		
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
