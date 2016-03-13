import sys, os, time
from collections import deque
from twisted.internet import reactor
from twisted.internet import task
from twisted.internet import defer
from twisted.internet.fdesc import readFromFD, writeToFD, setNonBlocking
from twisted.python.failure import Failure
from .client import Client
from .. import http, common
import logging
logger = logging.getLogger(__name__)


def _readFromFD(fd, callback):
	from twisted.internet.main import CONNECTION_LOST, CONNECTION_DONE
	try:
		output = os.read(fd, 1024*10000) # read up to 10MB
	except (OSError, IOError) as ioe:
		if ioe.args[0] in (errno.EAGAIN, errno.EINTR):
			return
		else:
			return CONNECTION_LOST
	if not output:
		return CONNECTION_DONE

	callback(output)

class FileDownloadResponse(object):
	def __init__(self, req, success, message=''):
		self.req = req
		self.success = success
		self.message = message

class Downloader():
	"""
	
	an async downloader built on top of the twisted project

	"""



	def __init__(self, scraper, cc=3, progress_check_interval=60, stop_when_no_progress_made=True):
		
		self.scraper = scraper
		self.client = Client(scraper)
		self.cc = cc
		self.progress_check_interval = progress_check_interval
		self.stop_when_no_progress_made = stop_when_no_progress_made

		self.q = deque() #working queue
		
		self.onhold = deque() #waiting queue

		# self._input_count = 0
		self._done_count = 0

		self._prev_stats = None

	def set_cc(self, cc):
		self.cc = cc

	def put(self, req, onhold = False):
		if not onhold:
			self.q.append(req)
		else:
			self.onhold.append(req)	

	def process(self):
		""" a generator used by Cooperator """
		while True:
			try:
				req = self.q.popleft()
				self._done_count +=1

				if req.get('bin') is True:
					d = self._download_file(req)
				else:	
					d = self._request(req)
				if d is not None:
					#add a timeout call on the deferred to prevent downloader hangout
					timeout = req.get('timeout') or 45
					timeout += 10
					reactor.callLater(timeout, d.cancel)

				yield d

			except Exception as e:
				#main queue finished
				break		


	def start(self):
		
		if len(self.q)==0 and len(self.onhold)==0:
			#nothing on queues
			return

		coop = task.Cooperator(started=True)
		generator = self.process()

		deferreds = []

		for i in xrange(self.cc):
			
			d = coop.coiterate(generator)
			
			deferreds.append(d)
				

		dl = defer.DeferredList(deferreds)	

		def dl_finish(reason=None):
			
			self.stop()


		dl.addBoth(dl_finish)

		if self.progress_check_interval:
			task.LoopingCall(self.progress).start(self.progress_check_interval)

			#make sure this task is triggered just once
			self.progress_check_interval = None

		if not reactor.running:
			reactor.run()

	def stop(self, result=''):
		
		if len(self.q):
				# new items have just been added to the q, so go back and start processing again.
				self.start()
				
		elif len(self.onhold):
			#copy the onhold to main q, then restart the downloader
			self.q = self.onhold
			self.onhold = deque()
			self.scraper.logger.info('process onhold items: %s', len(self.q))
			self.start()		

		else:
			
			#all items in both queues processed
			self.progress()
			self.scraper.logger.info('download finished')
			try:
				
				reactor.stop()
			except Exception:
				pass
			

	
	def progress(self):
		stats = dict(
			pending = len(self.q),
			onhold = len(self.onhold),
			done = int(self._done_count)
			)
		self.scraper.logger.info('pending: %s, done: %s, onhold: %s', stats['pending'], stats['done'], stats['onhold'])

		if self._prev_stats == stats and (stats['pending']>0 or stats['onhold']>0):
			#for some reason the downloader made no progress, try to stop it manually
			if self.stop_when_no_progress_made:
				if reactor.running:
					try:
						self.scraper.logger.warn('downloader stopped uncleanly')
						reactor.stop()
					except Exception:
						pass

		self._prev_stats = stats

	

	def _write_file(self, file_path, data):
		
		with open(file_path, 'w') as f:
			# d = Deferred()
			fd = f.fileno()
			setNonBlocking(fd)
			writeToFD(fd, data)
			# return d
	
	def _write_to_cache(self, url, post, data, file_name=None):
		
		file_name = file_name or self.scraper.cache.make_key(url=url,post=post)
		file_path = os.path.join(self.scraper.cache.location, file_name)
		return self._write_file(file_path, data)

	def _read_from_cache(self, url, post, file_name):
		d = defer.Deferred()

		file_name = file_name or self.scraper.cache.make_key(url=url,post=post)
		path = os.path.join(self.scraper.cache.location, file_name)
		with open(path, 'rb') as f:
			fd = f.fileno()
			setNonBlocking(fd)
			_readFromFD(fd, d.callback)
				
		return d

	def _build_response_data(self, req, response):
		
		encoding = 'utf8'
		unicode_html = u''

		try:
			unicode_html = response['data'].decode(encoding, 'ignore')
		except Exception as e:
			logger.warn('failed to decode bytes from url: %s', req.url)

		
		return_type = req.get('return_type') or 'doc'

		if return_type == 'doc':
			doc = http.Doc(url=req.url, html=unicode_html)
			doc.req = req
			doc.status.code = response['code']
			doc.status.message = response['message']
			return doc
		elif return_type == 'html':
			html = common.DataItem( unicode_html )
			html.req = req
			html.status = common.DataObject()
			html.status.code = response['code']
			html.status.message = response['message']
			return html
		
		else:
			self.scraper.logger.warn('unsupported return_type: %s', return_type)
			return None


	def _cb_fetch_finished(self, response):
		if isinstance(response, Failure):
			self.scraper.logger.warn('request cancelled: %s', req.url)
			return

		req = response['req']
		if response['success'] == True:
			if self.scraper.config['use_cache']:
				self._write_to_cache(req.url, req.post, data=response['data'], file_name = req.get('file_name'))
		else:
			#untested code
			if req.get('retries'):
				req.update({'retries': req['retries'] - 1})
				
				self.scraper.logger.debug('fetch error: %s -- %s, url: %s', response['code'], response['message'], req.url)
				self.scraper.logger.debug('retry: %s %s', req.url, req.post)
				# self._request(req)
				#put back the request into the queue
				self.put(req)
				return
			else:	
				self.scraper.logger.warn('fetch error: %s -- %s, url: %s', response['code'], response['message'], req.url)
			#end of untested code
				
		if req.get('cb'):
			cb_data = self._build_response_data(req, response)
			req.get('cb')(cb_data)

	


	def _request(self, req):
		if self.scraper.config['use_cache']:
			if self.scraper.cache.exists(url=req.url, post=req.post, file_name = req.get('file_name')):

				if req.get('cb'):
					def read_file_done(data):

						try:
							encoding = req.get('encoding') or 'utf8'
							cb_data = self._build_response_data(req, response = {'data': data, 'code': 200, 'message': 'ok' })
							req.get('cb')(cb_data)
						except Exception as e:
							self.scraper.logger.exception(e)	

					deferred = self._read_from_cache(req.url, req.post, req.get('file_name') )
					
					deferred.addCallback(read_file_done)


					return deferred
				else:
					#no need to return a deffered
					return None	

		
		deferred = self.client.fetch(req)
		deferred.addBoth(self._cb_fetch_finished)
		return deferred
		
	def _cb_file_downloaded(self, response, req, file_path):
		
		cb = req.get('cb')
		
		if isinstance(response, Failure):
			self.scraper.logger.warn('request cancelled: %s', req.url)
			if req.get('retries'):
				req.update({'retries': req['retries'] - 1})
				self.scraper.logger.debug('retry: %s %s', req.url, req.post)
				#put back the request into the queue
				self.put(req)
				return	

			if cb:
				cb(FileDownloadResponse(req=req, success=False, message='request cancelled'))

			return
				
		
		if response['success']:

			self._write_file(file_path, response['data'])
		else:
			if req.get('retries'):
				req.update({'retries': req['retries'] - 1})
				self.scraper.logger.debug('fetch error: %s -- %s, url: %s', response['code'], response['message'], req.url)
				self.scraper.logger.debug('retry: %s %s', req.url, req.post)
				#put back the request into the queue
				self.put(req)
				return	

		
		if cb:
			cb(FileDownloadResponse(req=req, success=response['success'], message=response['message']))
	
	
	def _download_file(self, req):
		cb = req.get('cb')

		file_name = req.get('file_name')
		if not file_name:
			
			if cb:
				cb(FileDownloadResponse(req=req, success=False, message='file_name not defined'))
			
			return None

		directory = req.get('dir') or 'images'	
		directory = self.scraper.join_path(directory)
		if not os.path.exists(directory):
			os.mkdir(directory)

		file_path = os.path.join(directory , file_name)
		if os.path.exists(file_path):
			#already downloaded
			if cb:
				cb(FileDownloadResponse(req=req, success=True, message='already downloaded'))
			return None
		

		deferred = self.client.fetch(req)
		deferred.addBoth(self._cb_file_downloaded, req, file_path)
		return deferred
			


