import sys, os, urlparse, time, zlib, json, re, codecs, logging, urllib2, urllib, httplib, contextlib, cookielib, random, socket

from cStringIO import StringIO
from gzip import GzipFile

import common, agent
from node import Node

meta_seperator = '=======META======'

class ProxyManager(object):
	
	""" for proxy rotation controlling """

	def __init__(self, proxy_file, proxy_auth=''):		
		self.proxy_file = proxy_file
		self.proxy_auth = proxy_auth
		self.proxies = []
		self.load_proxies()


	def load_proxies(self):		
		proxy_file = self.proxy_file

		if proxy_file:
			if not os.path.exists(proxy_file):
				raise Exception('proxy_file not found: {0}'.format(proxy_file))
			
			self.proxies = common.read_lines(proxy_file)

		return self	

	def random_proxy(self):
		if not self.proxies:
			return ''

		proxy = random.choice( self.proxies )	
		if self.proxy_auth and len(proxy.split(':')) == 2:
			proxy = '%s@%s' % (self.proxy_auth, proxy)

		#support proxy in ip:port:user:pass
		if len(proxy.split(':')) == 4:
			proxy_auth = ':'.join(proxy.split(':')[2:])
			proxy = ':'.join(proxy.split(':')[0:2])
			proxy = '%s@%s' % (proxy_auth, proxy)
			
			
		return proxy	

	def get_proxy(self, url=None):

		return self.random_proxy()
		


class Status():
	""" Represents a http request response status """

	def __init__(self, code=0, final_url='', error=''):
		self.code = code
		self.final_url = final_url
		self.error = error

	def __str__(self):

		return str("code: %s, error: %s, final_url: %s" % (self.code, self.error, self.final_url) )

class Request(object):	
	""" Represents a http request """

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

class Response(object):
	""" a wrapper for http response """
	def __init__(self, data, status):
		self.data = data
		self.status = status


class Doc(Node):
	def __init__(self, status=None, url='', html='<html></html>', passdata= {}, html_clean=None):		
		if html_clean:
			html = html_clean(html)

		Node.__init__(self, html)
		self.url = common.DataItem( url )
		self.passdata = passdata if passdata else {}
		self.status = status or Status(final_url=url)
		

		
		
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
	def form_data(self):
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


def create_opener(use_cookie=True, cj=None):
	if use_cookie:
		cj = cj or cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor( cj ))
		opener.cj = cj
		return opener
	else:
		return urllib2.build_opener()	

class Client(object):

	def __init__(self, scraper):

		self.scraper = scraper
		self.logger = logging.getLogger(__name__)
		
		self.opener = create_opener(use_cookie=True)

		socket.setdefaulttimeout(self.scraper.config.get('timeout', 45) )

	def load(self, req):
		""" returns a DOM Document"""
		html = self.load_html(req)
		doc = Doc(html=html, url = req.url, status= html.status, passdata = req.get('passdata', {}))

		return doc

	def load_html(self, req):
		""" returns a unicode html object """
		cache = self.scraper.cache
		accept_error_codes = req.get('accept_error_codes')
		if accept_error_codes is None:
			accept_error_codes = [404]


		if cache and cache.exists(url = req.url, post=req.post, file_name=req.get('file_name')) and req.get('use_cache'):
			return self._read_from_cache(url=req.url, post=req.post, file_name=req.get('file_name'))

		if req.get('use_cache') and req.get('cache_only') and not cache.exists(url = req.url, post=req.post, file_name=req.get('file_name')):
			html = common.DataItem('<html/>')
			html.status = Status()
			return html 	
			
		res = self.fetch_data(req)

		html = common.DataItem( res.data or '')
		status = res.status

		if (status.code == 200 or status.code in accept_error_codes)  and cache and req.get('use_cache'):
			self._write_to_cache(url=req.url, post=req.post, data=html, status=status, file_name=req.get('file_name'))

		html.status = status

		return html	

		
	def load_json(self, req):
		""" returns a json object """
		data = self.load_html(req)
		try:
			return json.loads(data)

		except:
			self.logger.exception('json decode error for url: %s --  post: %s', req.url, req.post or '')
			return None	
		
	
	def fetch_data(self, req):
		""" processes a http request specified by the req object and returns a response object """

		accept_error_codes = req.get('accept_error_codes')
		if accept_error_codes is None:
			accept_error_codes = [404]


		time.sleep(self.scraper.config['delay'])
		opener = req.get('opener')
		if not opener:
			opener = create_opener(use_cookie=False) if req.get('use_cookie') is False else  self.opener

		#default headers
		user_agent = req.get('user_agent', agent.firefox ) #default agent is firefox
		
		if user_agent == 'random':
			user_agent = agent.random_agent()

		headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"User-Agent": user_agent,
			"Accept-Language": "en-us,en;q=0.5",
			"Accept-Encoding": "gzip, deflate",			
			"Connection": "close" #turn off keep-alive
		}
		if req.post:
			headers.update({"Content-Type": "application/x-www-form-urlencoded"})
			
		#update user-passed in headers
		headers.update(req.get('headers', {})) 

			
		proxy = req.get('proxy') or self.scraper.proxy_manager.get_proxy(req.url)
		
		
		if proxy and req.get('use_proxy') is not False:
			if req.url.lower().startswith('https://'):
				opener.add_handler(urllib2.ProxyHandler({'https' : proxy}))
			else:
				opener.add_handler(urllib2.ProxyHandler({'http' : proxy}))
		
		#self.logger.debug('proxy: %s', proxy)

		#normalise the post
		if req.post and isinstance(req.post, common.MyDict):
			req.post = req.post.dict()
		if req.post and isinstance(req.post, dict):
			req.post = urllib.urlencode(sorted(req.post.items()))

		request = urllib2.Request(req.url, req.post, headers)
			
		tries = req.get('retries', 0)	
		
		status_code = 0
		error_message = ''
		final_url = None	

		
		self.logger.debug('loading %s %s', req.url, req.post or '')

		try:

			with contextlib.closing(opener.open(request, timeout= req.get('timeout', self.scraper.config['timeout']))) as res:
				final_url = res.url
				status_code = res.code


				rawdata = res.read()
				if 'gzip' in res.headers.get('content-encoding','').lower():
					bytes = zlib.decompress(rawdata, 16+zlib.MAX_WBITS)
				elif 'deflate' in res.headers.get('content-encoding','').lower():	
					bytes = zlib.decompressobj(-zlib.MAX_WBITS).decompress(rawdata)	
				else:
					bytes = rawdata

				encoding = req.get('encoding') or  common.DataItem(res.headers.get('content-type') or '').subreg('charset\s*=([^;]+)')	or 'utf8'
				content_type = res.headers.get('content-type', '').lower()

				#self.logger.debug('content type: %s, encoding: %s', content_type, encoding)
				
				data = ''

				#default is text data
				
				is_binary_data = req.get('bin') or False
				if 'image' in content_type or 'pdf' in content_type:
					is_binary_data = True

				if  not is_binary_data:
					data = bytes.decode(encoding, 'ignore')

					#verify data
					#self.logger.debug('contain: %s', req.get('contain'))
					if req.get('contain') and req.get('contain') not in data:
						raise Exception("invalid html, not contain: %s" % req.get('contain'))

					verify = req.get('verify')
					
					if verify and (not verify(data)):
						raise Exception("invalid html")
				else:
					
					#binary content
					data = bytes		

				return Response(data=data, status= Status(code=status_code, final_url=final_url))	

		
		except Exception, e:
			if status_code == 0 and hasattr(e,'code'):
				status_code = e.code
			if hasattr(e, 'reason'):
				error_message = e.reason			

			elif hasattr(e, 'line'):
				error_message = 'BadStatusLine: %s' % e.line

			elif hasattr(e, 'message'):	
				error_message =  e.message

			

			if not error_message and hasattr(e, 'args'):					
				error_message = u", ".join([str(item) for item in e.args]).replace("''",'unknown')	
				#self.logger.exception('fetch_data unknow error:') #test
		
			
			if tries > 0 and status_code not in accept_error_codes:
				#try to open the request one again	
				self.logger.debug('data fetching error: %s %s', status_code if status_code !=0 else '', error_message)
				req.update({'retries': tries - 1})
				return self.fetch_data(req)
			else:
				self.logger.warn('data fetching error: %s %s', status_code if status_code !=0 else '', error_message)	
				return Response(data=None, status = Status(code = status_code, final_url=final_url, error = error_message))





		

	def _read_from_cache(self, url, post, file_name=None):
		cache = self.scraper.cache

		cachedata = cache.read(url = url, post = post, file_name = file_name).split(meta_seperator)
		
		cachedhtml = None
		status = Status(code=200, final_url=None, error=None)
		if len(cachedata)==2:
			cachedhtml = cachedata[1]
			meta = json.loads( cachedata[0] )
			#reload status
			status = Status(code= meta['status']['code'], final_url = meta['status']['final_url'], error = meta['status'].get('error', '') )
		else:
			#no meta data
			cachedhtml = cachedata[0]
		html = common.DataItem(cachedhtml)	
		html.status = status

		return html

	def _write_to_cache(self, url, post, data, status, file_name=None):
		meta = {
				'url': url,
				'status': {
					'code': status.code,
					'final_url': status.final_url,
					'error': status.error
				}
			}
		
		self.scraper.cache.write(url=url, post=post, file_name=file_name, data=u''.join([json.dumps(meta), meta_seperator, data]) )	
	

		

