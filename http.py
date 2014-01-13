import urlparse, requests, time, zlib
from node import Node
from cache import Cache
import common

def open(req, errorhandler = None):

	#normalise the post
	if req.post and isinstance(req.post, basestring):
		req.post = dict(urlparse.parse_qsl(req.post))
		
	cache = req.get('cache') if isinstance(req.get('cache'), Cache) else None
	
	#try read from cache first
	if cache and cache.exists(url = req.url, post = req.post, filename = req.get('filename')):		
		return DOM(url=req.url, passdata = req.get('passdata'), html=cache.read(url = req.url, post = req.post, filename = req.get('filename')))


	client = req.get('client') if req.get('client') else requests


	#print 'client: ', type(client)	

	headers = req.get('headers', {
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2",
		"Accept-Language": "en-us,en;q=0.5",
		"Accept-Encoding": "gzip, deflate",	
		#"Connection": "keep-alive"
		"Connection": "close"
	})
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
			r = client.post(req.url, data = req.post, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream=True)
		else:	
			r = client.get(req.url, headers = headers, timeout = req.get('timeout'), proxies = proxies, verify = False, stream = True)
		
		if r.status_code != 200:
			raise Exception('Invalid status code: %s' % r.status_code)
		if 'gzip' in r.headers.get('content-encoding', ''):
			bytes = zlib.decompress(r.raw.read(), 16+zlib.MAX_WBITS)	
		else:
			bytes = r.raw.read()	

		if req.get('bin') is True:
			#download binary file
			return bytes

		html = bytes.decode(req.get('encoding', r.encoding), 'ignore')
		if req.get('contain') and req.get('contain') not in html:
			raise Exception("html not contain: %s", req.get('contain'))
		
		#write html to cache
		if cache:
			cache.write(url= req.url, post=req.post, filename = req.get('filename'), data = html) # in utf8 format
		
		return DOM(html=html, url = req.url, passdata = req.get('passdata'))		

	except Exception, e:		
		if tries > 0:
			#try to open the request one again	
			req.update({'retries': tries - 1})
			return open(req, errorhandler)

		if errorhandler:
			errorhandler(err = e, req = req, res = r)
		else:
			print e, 'url: ', req.url
				
		if req.get('bin') is True:
			return None
		else:		
			return DOM(url=req.url, passdata = req.get('passdata'), statuscode = r.status_code if r else -1)


class DOM(Node):
	def __init__(self, url='', html='<html></html>', passdata= {}, statuscode=200):		
		Node.__init__(self, html)
		self.url = url
		self.passdata = passdata if passdata else {}
		self.statuscode = statuscode

		
		
		#resolve relative urls
		baseurl = self.x("//base/@href").tostring()
		if not baseurl:
			baseurl = self.url

		for n in self.q('//a[@href and not(@href='') and not(contains(@href, "javascript")) and not(contains(@href, "#")) and not(contains(@href, "mailto:"))]'):					
			n.set('href', urlparse.urljoin(baseurl, n.get('href').tostring()))
		for n in self.q('//form[@action]'):					
			n.set('action', urlparse.urljoin(baseurl, n.get('action').tostring()))	
		for n in self.q('//img[@src]'):					
			n.set('src', urlparse.urljoin(baseurl, n.get('src').tostring()))		




class Request(object):	
	def __init__(self, url, post = None, **options):		
		self.url = url	
		self.post = post
		self.options = options

	def get(self, name, default = None):
		return self.options.get(name, default)
	def set(self, name, value):
		return self.options.set(name, value)	

	def update(self, dict2):
		self.options.update(dict2)
		return self
