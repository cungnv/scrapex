from time import time
from twisted.internet import reactor
from twisted.internet import task
from twisted.web.client import HTTPClientFactory, URI, HTTPPageGetter, Agent, ProxyAgent, RedirectAgent, BrowserLikeRedirectAgent, ContentDecoderAgent, GzipDecoder, CookieAgent
from twisted.internet.endpoints import HostnameEndpoint, TCP4ClientEndpoint
from twisted.internet.defer import Deferred
from twisted.internet import ssl
from twisted.web.http_headers import Headers
from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer
import random
from scrapex import common
from scrapex.async.agents import TunnelingAgent, ScrapexClientContextFactory
from scrapex.async.body_reader import readBody

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
					# logger.warn('no charset parsed from content_type: %s, assumed utf8, url: %s', content_type, req.url)
					charset = 'utf8'
					
				body = _to_utf8encoded_bytes(body, charset=charset)				


			result = {
					'success': True,
					'data': body, #in utf8-encoded bytes
					'req': req,
					'code': 200,
					'message': 'ok'

				}	

		try:	
			
			output_deferred.callback(result)

		except Exception as e:
			logger.debug(e.message)
		
			
	def body_err(err):
		logger.debug(err)
		result = {
				'success': False,
				'data': '',
				'req': req,
				'code': 0, #getattr(response, 'code', 0),
				'message': 'error while reading response body'

			}
		try:	
			output_deferred.callback(result)
		except Exception as e:
			logger.debug(e.message)
		

	accept_error_codes = req.get('accept_error_codes') or []

	if response.code != 200 and response.code not in accept_error_codes:
		#failed
		result = {
				'success': False,
				'data': '',
				'req': req,
				'code': response.code,
				'message': 'error'

			}
		try:	
			output_deferred.callback(result)
		except Exception as e:
			logger.debug(e.message)

	else:
		#success
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

	try:	
		output_deferred.callback(result)
	except Exception as e:
		logger.debug(e.message)
	


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
	"""	
	todo:
	- when proxies used, make sure each request uses random proxy
	- test the number of persistent connections
	- use a pool of agents?

	"""
	def __init__(self, scraper, pool=None):
		self.scraper = scraper
		self._pool = pool

		self._agents = {} #map proxy->an agent


		redirectLimit = scraper.config.get('max_redirects')
		if redirectLimit is None:
			redirectLimit = 3

		#create an agent for direct requests
		self._direct_agent = Agent(reactor, pool=self._pool, connectTimeout=scraper.config.get('timeout') or 30)
		if redirectLimit>0:
			self._direct_agent = BrowserLikeRedirectAgent(self._direct_agent, redirectLimit=redirectLimit)
		
		self._direct_agent = ContentDecoderAgent(self._direct_agent, [('gzip', GzipDecoder)])
		self.cj = self.scraper.client.opener.cj
		

		if self.cj is not None:
			
			self._direct_agent = CookieAgent(self._direct_agent, self.cj)

		#create an agent for http-proxy requests
		#no endpoint yet, use __ instead of _ to backup the instance
		self.__http_proxy_agent = ProxyAgent(None, pool=self._pool) 

		if redirectLimit>0:
			self._http_proxy_agent = BrowserLikeRedirectAgent(self.__http_proxy_agent, redirectLimit=redirectLimit)

			self._http_proxy_agent = ContentDecoderAgent(self._http_proxy_agent, [('gzip', GzipDecoder)])
		else:

			self._http_proxy_agent = ContentDecoderAgent(self.__http_proxy_agent, [('gzip', GzipDecoder)])
			

		if self.cj is not None:
			self._http_proxy_agent = CookieAgent(self._http_proxy_agent, self.cj)

		#create an agent for https-proxy requests
		#no endpoint yet, use __ instead of _ to backup the instance
		self.__https_proxy_agent = TunnelingAgent(reactor=reactor, proxy=None, contextFactory=ScrapexClientContextFactory(), connectTimeout=30, pool=self._pool) #no proxy yet
		if redirectLimit>0:
			self._https_proxy_agent = BrowserLikeRedirectAgent(self.__https_proxy_agent, redirectLimit=redirectLimit)

			self._https_proxy_agent = ContentDecoderAgent(self._https_proxy_agent, [('gzip', GzipDecoder)])
		else:
			self._https_proxy_agent = ContentDecoderAgent(self.__https_proxy_agent, [('gzip', GzipDecoder)])

			
		if self.cj is not None:
			self._https_proxy_agent = CookieAgent(self._https_proxy_agent, self.cj)


	def _create_agent(self, req):

		""" create right agent for specific request """

		agent = None

		uri = URI.fromBytes(req.url)
		proxy = req.get('proxy')
		if req.get('use_proxy') is False:
			proxy = None
		
		if proxy:	
			if uri.scheme == 'https':
				
				agent_key = 'httpsproxy-%s-%s' % (proxy.host, proxy.port)
				agent = self._agents.get(agent_key)

				if not agent:
					
					agent = TunnelingAgent(reactor=reactor, proxy=proxy, contextFactory=ScrapexClientContextFactory(), connectTimeout=30, pool=self._pool)

					self._agents[agent_key] = agent

			else:
				#http
				agent_key = 'httpproxy-%s-%s' % (proxy.host, proxy.port)
				agent = self._agents.get(agent_key)

				if not agent:
					endpoint = TCP4ClientEndpoint(reactor, host=proxy.host, port=proxy.port , timeout=req.get('timeout'))
					agent = ProxyAgent(endpoint, pool=self._pool)
					self._agents[agent_key] = agent


				if proxy.auth_header:
					req.get('headers')['Proxy-Authorization'] = proxy.auth_header

		else:
			
			agent = self._direct_agent #use single agent when no proxies used


		redirectLimit = self.scraper.config.get('max_redirects')
		if redirectLimit is None:
			redirectLimit = 3
	
		if redirectLimit>0:
			agent = BrowserLikeRedirectAgent(agent, redirectLimit=redirectLimit)

		
		agent = ContentDecoderAgent(agent, [('gzip', GzipDecoder)])

		if self.cj is not None:
			agent = CookieAgent(agent, self.cj)
		
		return agent	

	def fetch(self, req):

		req.normalize(self.scraper)

		""" select agent and install proxy if required """
		
		# agent = None

		# uri = URI.fromBytes(req.url)
		# proxy = req.get('proxy')
		# if req.get('use_proxy') is False:
		# 	proxy = None
		# if proxy:	
		# 	if uri.scheme == 'https':

		# 		agent = self._https_proxy_agent
		# 		#install proxy for this request

		# 		self.__https_proxy_agent.set_proxy(proxy)

		# 	else:
		# 		agent = self._http_proxy_agent
		# 		#install proxy for this request
		# 		self.__http_proxy_agent._proxyEndpoint = TCP4ClientEndpoint(reactor, host=proxy.host, port=proxy.port , timeout=req.get('timeout'))
		# 		if proxy.auth_header:
		# 			req.get('headers')['Proxy-Authorization'] = proxy.auth_header
		# else:
		# 	agent = self._direct_agent
		
		agent = self._create_agent(req) #use one agent per request to rotate proxies
		
		headers = req.get('headers')
		
		_headers = {}
		for key in headers:
			_headers[key] = [headers[key]]

		_headers = 	Headers(_headers)
		
		if self.scraper.config['debug']:
			self.scraper.logger.debug('to fetch: %s', req.url)
		
		bodyProducer = StringProducer(req.post) if req.post else None
		delay =  req['delay'] + random.random()
		deferred = task.deferLater(reactor, delay, agent.request, uri= req.url, method='POST' if req.post else 'GET', bodyProducer=bodyProducer,  headers=_headers)
		# deferred = agent.request(uri= req.url, method='POST' if req.post else 'GET', bodyProducer=bodyProducer,  headers=_headers)


		def _canceller(ignore):
			
			""" 
			will be called by the downloader when the request take too much time 
			
			the output_deferred's errback will be fired, where it may re-schedule the request

			"""
			#todo: test this code
			#cancel the deferred returned by agent.request
			
			self.scraper.logger.debug('cancel request: %s', req.url)

			deferred.cancel() #will fire its errback, then in turn will fire output_deferred's callback with a failed response

			""" end of experimental code """

			#check to see whether to retry this request or not
			# if req.get('retries') > 0:
			# 	req.update({'retries': req['retries'] - 1})
				
			# 	self.scraper.logger.debug('request timeouted: %s', req.url)

			# 	self.scraper.logger.debug('re-schedule(%s): %s %s', req.get('retries'), req.url, req.post)
				
			# 	#put back the request into the queue
			# 	self.scraper.downloader.putleft(req)
				
			# else:	
			# 	self.scraper.logger.warn('request cancelled: %s', req.url)	


		output_deferred = Deferred(_canceller)

		deferred.addCallback(_handle_response, req, output_deferred)
		deferred.addErrback(_handle_err, req, output_deferred)
		

		return output_deferred


if __name__ == '__main__':
	pass
			


		