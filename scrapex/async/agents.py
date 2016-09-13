"""
This module is taken and customized from the Scrapy project:
https://github.com/scrapy/scrapy
"""

from time import time
import re
from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory, URI, HTTPPageGetter, Agent, ProxyAgent, RedirectAgent, ContentDecoderAgent, GzipDecoder
from twisted.internet.endpoints import HostnameEndpoint, TCP4ClientEndpoint
from twisted.web.http import HTTPClient
from twisted.internet import defer
from twisted.web.http_headers import Headers
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.internet import ssl
from OpenSSL import SSL
from twisted.internet.ssl import ClientContextFactory
import base64
from zope.interface import implementer
from twisted.internet import interfaces

from scrapex import common

class TunnelError(Exception):
	"""An HTTP CONNECT tunnel could not be established by the proxy."""


class TunnelingTCP4ClientEndpoint(TCP4ClientEndpoint):
	"""An endpoint that tunnels through proxies to allow HTTPS downloads. To
	accomplish that, this endpoint sends an HTTP CONNECT to the proxy.
	The HTTP CONNECT is always sent when using this endpoint, I think this could
	be improved as the CONNECT will be redundant if the connection associated
	with this endpoint comes from the pool and a CONNECT has already been issued
	for it.
	"""

	_responseMatcher = re.compile(b'HTTP/1\.. 200')

	def __init__(self, reactor, host, port, proxy, contextFactory,
				 timeout=30, bindAddress=None):
		super(TunnelingTCP4ClientEndpoint, self).__init__(reactor, proxy.host,
			proxy.port, timeout, bindAddress)
		
		self._tunnelReadyDeferred = defer.Deferred()
		self._tunneledHost = host
		self._tunneledPort = port
		self._contextFactory = contextFactory
		self._proxy = proxy

	def requestTunnel(self, protocol):
		"""Asks the proxy to open a tunnel."""

		tunnelReq = 'CONNECT %s:%s HTTP/1.1\r\n' % ( self._tunneledHost, self._tunneledPort)
		if self._proxy.auth_header:
			tunnelReq += 'Proxy-Authorization: ' + self._proxy.auth_header + '\r\n'

		tunnelReq += '\r\n'
		protocol.transport.write(tunnelReq)
		self._protocolDataReceived = protocol.dataReceived
		protocol.dataReceived = self.processProxyResponse
		self._protocol = protocol
		return protocol

	def processProxyResponse(self, bytes):
		"""Processes the response from the proxy. If the tunnel is successfully
		created, notifies the client that we are ready to send requests. If not
		raises a TunnelError.
		"""
		self._protocol.dataReceived = self._protocolDataReceived
		if  TunnelingTCP4ClientEndpoint._responseMatcher.match(bytes):
			
			# print 'test: requestTunnel successfully'

			self._protocol.transport.startTLS(self._contextFactory,
											  self._protocolFactory)
			self._tunnelReadyDeferred.callback(self._protocol)

		else:
			
			# print 'test: requestTunnel failed'

			self._tunnelReadyDeferred.errback(
				TunnelError('Could not open CONNECT tunnel.'))

	def connectFailed(self, reason):
		"""Propagates the errback to the appropriate deferred."""
		self._tunnelReadyDeferred.errback(reason)

	def connect(self, protocolFactory):
		self._protocolFactory = protocolFactory
		connectDeferred = super(TunnelingTCP4ClientEndpoint,
								self).connect(protocolFactory)
		connectDeferred.addCallback(self.requestTunnel)
		connectDeferred.addErrback(self.connectFailed)
		return self._tunnelReadyDeferred


class TunnelingAgent(Agent):
	"""An agent that uses a L{TunnelingTCP4ClientEndpoint} to make HTTPS
	downloads. It may look strange that we have chosen to subclass Agent and not
	ProxyAgent but consider that after the tunnel is opened the proxy is
	transparent to the client; thus the agent should behave like there is no
	proxy involved.
	"""

	def __init__(self, reactor, proxy, contextFactory=None,
				 connectTimeout=None, bindAddress=None, pool=None):
		super(TunnelingAgent, self).__init__(reactor, contextFactory,
			connectTimeout, bindAddress, pool)
			
		self._proxy = proxy
		self._contextFactory = contextFactory

	def _getEndpoint(self, uri):

		return TunnelingTCP4ClientEndpoint(
			self._reactor, uri.host, uri.port, self._proxy,
			self._contextFactory, self._endpointFactory._connectTimeout,
			self._endpointFactory._bindAddress)
	
	def set_proxy(self, proxy):
		self._proxy = proxy




class ScrapexClientContextFactory(ClientContextFactory):
	def __init__(self):
		self.method = SSL.TLSv1_METHOD
	
	def getContext(self, hostname=None, port=None):
		ctx = ClientContextFactory.getContext(self)
		ctx.set_options(SSL.OP_ALL)
		if hostname and ClientTLSOptions is not None: # workaround for TLS SNI
			ClientTLSOptions(hostname, ctx)
		return ctx


def build_agent(req):
	uri = URI.fromBytes(req.url)
	proxy = req.get('proxy')
	if req.get('use_proxy') is False:
		proxy = None

	if proxy:	
		if uri.scheme == 'https':

			agent = TunnelingAgent(reactor=reactor, proxy=proxy, contextFactory=ScrapexClientContextFactory(), connectTimeout=req.get('timeout'))
		else:
			endpoint = TCP4ClientEndpoint(reactor, host=proxy.host, port=proxy.port , timeout=req.get('timeout'))
			agent = ProxyAgent(endpoint)	
			if proxy.auth_header:
				req.get('headers')['Proxy-Authorization'] = proxy.auth_header
	else:
		agent = Agent(reactor)

	agent = RedirectAgent(agent, redirectLimit=3)
	agent = ContentDecoderAgent(agent, [('gzip', GzipDecoder)])
	return agent


if __name__ == '__main__':
	pass


