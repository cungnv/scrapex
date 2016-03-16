from time import time
from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory, URI, HTTPPageGetter, Agent, ProxyAgent, RedirectAgent, BrowserLikeRedirectAgent, ContentDecoderAgent, GzipDecoder, CookieAgent
from twisted.internet.endpoints import HostnameEndpoint, TCP4ClientEndpoint
from twisted.internet.defer import Deferred
from twisted.internet import ssl
from twisted.web.http_headers import Headers
from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer

from .. import common
from .agents import TunnelingAgent, ScrapexClientContextFactory
from .body_reader import readBody

import logging
logger = logging.getLogger(__name__)

def _to_utf8encoded_bytes(bytes, charset):
	if charset.replace('-','').lower() == 'utf8':
		#return as is
		return bytes
	if not charset:
		charset = 'utf8'

	unicode_string = None	
	try:
		unicode_string = bytes.decode(charset, 'ignore')
	except:
		#try with latin1
		try:
			unicode_string = bytes.decode('latin1', 'ignore')
		except:
			logger.warn('failed to decode bytes from url: %s', req.url)

	if unicode_string:
		return unicode_string.encode('utf8')
	else:
		#return as-is
		return bytes	



def _handle_response(response, req, output_deferred):

	if response.code != 200:
		result = {
				'success': False,
				'data': '',
				'req': req,
				'code': response.code,
				'message': 'error'

			}
		output_deferred.callback(result)
		return
	
	def body_ready(body):
		if req.get('contain') and req.get('contain') not in body:
			result = {
					'success': False,
					'data': body,
					'req': req,
					'code': 200,
					'message': 'not contain text: %s' % req.get('contain')
					
				}
		else:
			#success
			content_type = response.headers.getRawHeaders('content-type')
			if not content_type:
				logger.warn('no content-type header found: %s', req.url)
				content_type = ''
			else:
				content_type = content_type[0].lower()

			is_binary_data = req.get('bin') or False
			if 'image' in content_type or 'pdf' in content_type:
				is_binary_data = True

			if not is_binary_data:
				charset = common.DataItem(content_type).subreg('charset\s*=\s*([^\s]+)')
				if not charset:
					logger.warn('no charset parsed from content_type: %s, assumed utf8, url: %s', content_type, req.url)
					charset = 'utf8'
					
				body = _to_utf8encoded_bytes(body, charset=charset)				


			result = {
					'success': True,
					'data': body, #in utf8-encoded bytes
					'req': req,
					'code': 200,
					'message': 'ok'

				}	

		output_deferred.callback(result)
			
	def body_err(err):
		result = {
				'success': False,
				'data': '',
				'req': req,
				'code': 0, #getattr(response, 'code', 0),
				'message': 'error while reading response body'

			}
		output_deferred.callback(result)


	d = readBody(response)
	d.addCallbacks(body_ready, body_err)	
	
	
def _handle_err(err, req, output_deferred):
	result = {
				'success': False,
				'data': '',
				'req': req,
				'code': getattr(err,'code', 0),
				'message': err.getErrorMessage()

			}

	output_deferred.callback(result)		


class StringProducer(object):
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = body
		self.length = len(body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass

class Client(object):
	def __init__(self, scraper):
		self.scraper = scraper

		#create an agent for direct requests
		self._direct_agent = Agent(reactor)
		self._direct_agent = BrowserLikeRedirectAgent(self._direct_agent, redirectLimit=3)
		self._direct_agent = ContentDecoderAgent(self._direct_agent, [('gzip', GzipDecoder)])
		self.cj = self.scraper.client.opener.cj
		

		if self.cj is not None:
			
			self._direct_agent = CookieAgent(self._direct_agent, self.cj)

		#create an agent for http-proxy requests
		self.__http_proxy_agent = ProxyAgent(None) #no endpoint yet
		self._http_proxy_agent = BrowserLikeRedirectAgent(self.__http_proxy_agent, redirectLimit=3)
		self._http_proxy_agent = ContentDecoderAgent(self._http_proxy_agent, [('gzip', GzipDecoder)])

		if self.cj is not None:
			self._http_proxy_agent = CookieAgent(self._http_proxy_agent, self.cj)

		#create an agent for https-proxy requests
		self.__https_proxy_agent = TunnelingAgent(reactor=reactor, proxy=None, contextFactory=ScrapexClientContextFactory(), connectTimeout=30) #no proxy yet
		self._https_proxy_agent = BrowserLikeRedirectAgent(self.__https_proxy_agent, redirectLimit=3)
		self._https_proxy_agent = ContentDecoderAgent(self._https_proxy_agent, [('gzip', GzipDecoder)])
		if self.cj is not None:
			self._https_proxy_agent = CookieAgent(self._https_proxy_agent, self.cj)




	def fetch(self, req):
		
		req.normalize(self.scraper)
		
		""" select agent and install proxy if required """
		agent = None

		uri = URI.fromBytes(req.url)
		proxy = req.get('proxy')
		if req.get('use_proxy') is False:
			proxy = None
		if proxy:	
			if uri.scheme == 'https':

				agent = self._https_proxy_agent
				#install proxy for this request
				self.__https_proxy_agent.set_proxy(proxy)

			else:
				agent = self._http_proxy_agent
				#install proxy for this request
				self.__http_proxy_agent._proxyEndpoint = TCP4ClientEndpoint(reactor, host=proxy.host, port=proxy.port , timeout=req.get('timeout'))
				if proxy.auth_header:
					req.get('headers')['Proxy-Authorization'] = proxy.auth_header
		else:
			agent = self._direct_agent

		headers = req.get('headers')
		
		_headers = {}
		for key in headers:
			_headers[key] = [headers[key]]

		_headers = 	Headers(_headers)
		self.scraper.logger.debug('to fetch: %s %s', req.url, req.post)
		
		bodyProducer = StringProducer(req.post) if req.post else None

		deferred = agent.request(uri= req.url, method='POST' if req.post else 'GET', bodyProducer=bodyProducer,  headers=_headers)

		output_deferred = Deferred()

		deferred.addCallback(_handle_response, req, output_deferred)
		deferred.addErrback(_handle_err, req, output_deferred)
		

		return output_deferred


if __name__ == '__main__':
	pass
			


		