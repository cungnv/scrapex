from time import time
from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory, URI
from twisted.internet.defer import Deferred
from twisted.internet import ssl

from .. import common
from .tunnel import Tunnel

def _handle_response(response, req, output_deferred):
	if req.get('contain') and req.get('contain') not in response:
		result = {
				'success': False,
				'data': response,
				'req': req,
				'code': 200,
				'message': 'not contain text: %s' % req.get('contain')
				
			}
	else:
		result = {
				'success': True,
				'data': response,
				'req': req,
				'code': 200,
				'message': 'ok'

			}	
	output_deferred.callback(result)
			


	
def _handle_err(err, req, output_deferred):
	result = {
				'success': False,
				'data': '',
				'req': req,
				'code': getattr(err,'code', 0),
				'message': err.getErrorMessage()

			}

	output_deferred.callback(result)		

def fetch(req, scraper):
	
	req.normalise(scraper)

	headers = req.get('headers')
	
	factory = HTTPClientFactory(url=req.url, headers=headers)
	
	if req.url.lower().startswith('https'):
		contextFactory = ssl.ClientContextFactory()
	else:
		contextFactory = None

	proxy = req.get('proxy')
	if req.get('use_proxy') is False:
		proxy = None

	tunnel = Tunnel(proxy)

	tunnel.connect(factory.host, factory.port, factory, contextFactory)
	output_deferred = Deferred()

	factory.deferred.addCallback(_handle_response, req, output_deferred)
	factory.deferred.addErrback(_handle_err, req, output_deferred)
	

	return output_deferred


if __name__ == '__main__':
	pass
			


		