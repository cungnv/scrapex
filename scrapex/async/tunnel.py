from twisted.internet import protocol, reactor

class HTTPSTunnelOutputProtocol(protocol.Protocol):
	def __init__(self):
		
		self.data = ""
		self.dataState = 0
		
	def connectionMade(self):
		
		request = "CONNECT %s:%s HTTP/1.1\r\n" % (self.factory.host, self.factory.port)
		
		if self.factory.proxy.auth_header:
			request += 'Proxy-Authorization: %s\r\n' % self.factory.proxy.auth_header

		request += '\r\n'	#finish command

		self.transport.write(request)
		
	def connectionLost(self, reason):
		print 'connectionLost: ', reason

	def dataReceived(self, data):

		self.data = self.data + data
		if self.dataState == 0:
			if self.processDataState0():
				return
	
	def processDataState0(self):
		self.factory.tunnelProtocol.tunnelOutputProtocol_connectionMade('')
		return

		data = self.data
		
		i = data.find("\r\n\r\n")
		
		if i == -1:
			return True
			
		i = i + 4
		
		response = data[:i]
		
		data = data[i:]
		
		responseLines = response.split("\r\n")
		responseLine = responseLines[0].split(" ", 2)
		
		if len(responseLine) != 3:
			self.transport.loseConnection()
			
			return True
		
		responseVersion = responseLine[0].upper()
		responseStatus = responseLine[1]
		responseStatusMessage = responseLine[2]
		
		if responseStatus != "200":
			self.transport.loseConnection()
			
			return True
		self.factory.tunnelProtocol.tunnelOutputProtocol_connectionMade(data)
		
		self.data = ""
		
		return True

class HTTPSTunnelOutputProtocolFactory(protocol.ClientFactory):
	protocol = HTTPSTunnelOutputProtocol
	
	def __init__(self, proxy, host, port):
		
		self.proxy = proxy
		self.host = host
		self.port = port
		self.tunnelProtocol = None
	
	def startedConnecting(self, connector):
		pass

	def clientConnectionFailed(self, connector, reason):
		pass
	
	def clientConnectionLost(self, connector, reason):
		pass


class TunnelProtocol(protocol.Protocol):
	
	def connectionMade(self):
		
		self.factory.tunnelOutputProtocolFactory.tunnelProtocol = self
		self.factory.tunnelOutputProtocol = self.factory.tunnelOutputProtocolFactory.buildProtocol(self.transport.getPeer())
		self.factory.tunnelOutputProtocol.makeConnection(self.transport)
	
	def connectionLost(self, reason):
		
		if self.factory.tunnelOutputProtocol is not None:
			self.factory.tunnelOutputProtocol.connectionLost(reason)
		else:
			if self.factory.outputProtocol is not None:
				self.factory.outputProtocol.connectionLost(reason)
	
	def dataReceived(self, data):
		
		if self.factory.tunnelOutputProtocol is not None:
			self.factory.tunnelOutputProtocol.dataReceived(data)
		else:
			if self.factory.outputProtocol is not None:
				self.factory.outputProtocol.dataReceived(data)
	
	def tunnelOutputProtocol_connectionMade(self, data):
		
		self.factory.tunnelOutputProtocol = None
		
		if self.factory.contextFactory is not None:
			self.transport.startTLS(self.factory.contextFactory)
		
		self.factory.outputProtocol = self.factory.outputProtocolFactory.buildProtocol(self.transport.getPeer())
		self.factory.outputProtocol.makeConnection(self.transport)
		
		if len(data) > 0:
			self.factory.outputProtocol.dataReceived(data)

class TunnelProtocolFactory(protocol.ClientFactory):
	protocol = TunnelProtocol
	
	def __init__(self, outputProtocolFactory, tunnelOutputProtocolFactory, contextFactory=None):
		
		self.outputProtocol = None
		self.outputProtocolFactory = outputProtocolFactory
		self.tunnelOutputProtocol = None
		self.tunnelOutputProtocolFactory = tunnelOutputProtocolFactory
		self.contextFactory = contextFactory
	
	def startedConnecting(self, connector):
		
		self.outputProtocolFactory.startedConnecting(connector)
	
	def clientConnectionFailed(self, connector, reason):
		
		self.outputProtocolFactory.clientConnectionFailed(connector, reason)
	
	def clientConnectionLost(self, connector, reason):
		
		if self.outputProtocol is None:
			self.outputProtocolFactory.clientConnectionFailed(connector, reason)
		else:
			self.outputProtocolFactory.clientConnectionLost(connector, reason)

class Tunnel(object):
	def __init__(self, proxy):
		
		self.proxy = proxy
	
	def connect(self, host, port, outputProtocolFactory, contextFactory=None, timeout=30, bindAddress=None):
		
		if self.proxy is None:
			#no proxy, directly connect
			if contextFactory is None:
				return reactor.connectTCP(host, port, outputProtocolFactory, timeout, bindAddress)
			else:
				return reactor.connectSSL(host, port, outputProtocolFactory, contextFactory, timeout, bindAddress)
		else:
			if contextFactory:
				#HTTPS proxying
				tunnelOutputProtocolFactory = HTTPSTunnelOutputProtocolFactory(self.proxy, host, port)
				
				tunnelProtocolFactory = TunnelProtocolFactory(outputProtocolFactory, tunnelOutputProtocolFactory, contextFactory)
				
				return reactor.connectTCP(self.proxy.host, self.proxy.port, tunnelProtocolFactory, timeout, bindAddress)
			else:
				#HTTP proxying

				outputProtocolFactory.path = outputProtocolFactory.url
				
				if self.proxy.auth_header:
					outputProtocolFactory.headers['Proxy-Authorization'] = self.proxy.auth_header

				return reactor.connectTCP(self.proxy.host, self.proxy.port, outputProtocolFactory, timeout, bindAddress)
					
		
	
