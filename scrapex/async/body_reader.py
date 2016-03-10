import os
import warnings
from twisted.web._newclient import PotentialDataLoss
from twisted.web._newclient import ResponseDone, ResponseFailed
from twisted.web._newclient import RequestNotSent, RequestTransmissionFailed
from twisted.internet import defer, protocol, task, reactor
from twisted.web.client import PartialDownloadError

class _ReadBodyProtocol(protocol.Protocol):
	"""
	Protocol that collects data sent to it.
	This is a helper for L{IResponse.deliverBody}, which collects the body and
	fires a deferred with it.
	@ivar deferred: See L{__init__}.
	@ivar status: See L{__init__}.
	@ivar message: See L{__init__}.
	@ivar dataBuffer: list of byte-strings received
	@type dataBuffer: L{list} of L{bytes}
	"""

	def __init__(self, status, message, deferred):
		"""
		@param status: Status of L{IResponse}
		@ivar status: L{int}
		@param message: Message of L{IResponse}
		@type message: L{bytes}
		@param deferred: deferred to fire when response is complete
		@type deferred: L{Deferred} firing with L{bytes}
		"""
		self.deferred = deferred
		self.status = status
		self.message = message
		self.dataBuffer = []


	def dataReceived(self, data):
		"""
		Accumulate some more bytes from the response.
		"""
		self.dataBuffer.append(data)


	def connectionLost(self, reason):
		"""
		Deliver the accumulated response bytes to the waiting L{Deferred}, if
		the response body has been completely received without error.
		"""
		# print self.dataBuffer
		
		if reason.check(ResponseDone):
			self.deferred.callback(b''.join(self.dataBuffer))
		elif reason.check(PotentialDataLoss):
			try:
				self.deferred.errback(
					PartialDownloadError(self.status, self.message,
										 b''.join(self.dataBuffer)))
			except Exception as ex:
				print ex
				self.deferred.errback(PartialDownloadError(0, 'PartialDownloadError', ''))	
		else:
			self.deferred.errback(reason)



def readBody(response):
	"""
	Get the body of an L{IResponse} and return it as a byte string.
	This is a helper function for clients that don't want to incrementally
	receive the body of an HTTP response.
	@param response: The HTTP response for which the body will be read.
	@type response: L{IResponse} provider
	@return: A L{Deferred} which will fire with the body of the response.
		Cancelling it will close the connection to the server immediately.
	"""
	def cancel(deferred):
		"""
		Cancel a L{readBody} call, close the connection to the HTTP server
		immediately, if it is still open.
		@param deferred: The cancelled L{defer.Deferred}.
		"""
		abort = getAbort()
		if abort is not None:
			abort()

	d = defer.Deferred(cancel)
	protocol = _ReadBodyProtocol(response.code, response.phrase, d)
	def getAbort():
		return getattr(protocol.transport, 'abortConnection', None)

	response.deliverBody(protocol)

	if protocol.transport is not None and getAbort() is None:
		warnings.warn(
			'Using readBody with a transport that does not have an '
			'abortConnection method',
			category=DeprecationWarning,
			stacklevel=2)

	return d

if __name__ == '__main__':
	e = PartialDownloadError(400, 'data lost', 'some data')
	print e