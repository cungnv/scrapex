import threading, os, random, sys, time, json, logging, logging.config, atexit
from Queue import Queue
from urlparse import urlparse

from node import Node
from worker import Worker
import http, common, logging_config
from http import Request
from cache import Cache


class Scraper(object):
	

	def __init__(self, **options):		

		_dir = os.path.dirname(sys.executable) if 'python' not in sys.executable.lower() else os.path.dirname( os.path.join( os.getcwd(), sys.argv[0] ) )
		

		self.config = dict(
			dir = _dir,			
			use_cache = True, 
			cache_path = "cache",
			use_proxy = True, 			
			use_cookie = True,						
			timeout = 45,
			delay = 0.1,
			retries = 0,
			parse_log = True,
			show_status_message = True

			)


		
		self.config.update(options)

		#expose important attributes
		self.dir = self.config.get('dir')
		if not os.path.exists(self.dir): os.makedirs(self.dir)		

		#load settings from local settings.txt
		if os.path.exists(self.join_path('settings.txt')):
			self.config.update(json.loads(common.get_file(self.join_path('settings.txt'))))

		if self.config['use_cache']:
			cache_path = os.path.join(self.dir, self.config['cache_path'])	

			self.cache = Cache(cache_path)
		else:
			self.cache = None	
		

		""" logging settings """
		if self.config.get('use_logging_config') is not False:
			#by default, config the logging
			if os.path.exists(self.join_path('logging.config')):
				logging.config.dictConfig(json.loads(common.get_file(self.join_path('logging.config'))))
			else:
				default_log_settings = logging_config.default_settings
				default_log_settings['handlers']['file_handler']['filename'] = self.join_path('log.txt')
				if self.config.get('debug') is True:
					default_log_settings['handlers']['console']['level'] = 'DEBUG'

				logging.config.dictConfig(default_log_settings)	

			#clear the log	
			if not self.config.get('preserve_log'):
				self.put_file(self.join_path('log.txt'), '')		


		self.logger = logging.getLogger(__name__)

		if self.config['show_status_message']:

			self.logger.info('start')
		
		atexit.register(self.__del__)

			
			
		self.proxy_manager = http.ProxyManager(proxy_file= self.join_path( self.config.get('proxy_file') ) if self.config.get('proxy_file') else None, proxy_auth=self.config.get('proxy_auth'))
		
		self.client = http.Client(scraper=self)
		
		#set flags
		self.writingflag = False

		#init the output db
		self.outdb = {}
	
	def get_log_stats(self):
		log_file = self.join_path('log.txt')
		if not os.path.exists(log_file):
			return ''
		else:
			logdata = common.parse_log(log_file)
			if logdata['errors'] == 0 and logdata['warnings'] == 0:
				return 'no warnings, no errors'
			else:
				return '%s warning(s) and %s error(s)' % ( logdata['warnings'], logdata['errors'] )

	
	def  __del__(self):
		
		self.flush()
		if self.config['show_status_message']:
			#parse log
			log_file = self.join_path('log.txt')
			
			if not os.path.exists(log_file) or self.config['parse_log'] is False:
				self.logger.info('Completed')
			else:
				logdata = common.parse_log(log_file)
				if logdata['errors'] == 0 and logdata['warnings'] == 0:
					self.logger.info('Completed successfully')
				else:
					self.logger.info('Completed with %s warning(s) and %s error(s)', logdata['warnings'], logdata['errors'])



	
	def join_path(self, file_name):
		return os.path.join(self.dir, file_name)
	def read_lines(self, file_name):
		return common.read_lines(self.join_path(file_name))	

	def write_json(self, file_name, data):
		common.write_json(self.join_path(file_name), data)
		return self
	def read_json(self, file_name):
		return common.read_json(self.join_path(file_name))

	def clear_cookies(self):
		self.client = http.Client(scraper=self)
		return self

	
	def load(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load(Request(url = url, post = post, **options))
	
	def load_html(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load_html(Request(url = url, post = post, **options))
	
	def load_json(self, url, post=None, **_options):		
		options = common.combine_dicts(self.config, _options)		
		
		return self.client.load_json(Request(url = url, post = post, **options))
			

	def save_link(self, url, dir='images', file_name='auto', format='jpg', prefix='', **_options):
		fn = ''
		if file_name == 'auto':			
			#special name
			fn = common.subreg(url, '/([^/\?\$]+\.[a-z]{2,4})$--is')			
			if not fn:
				self.logger.warn( 'failed to parse file_name from url: %s', url )
				return None

		elif not common.subreg(file_name, '(\.[a-z]{2,4})$--is'):			
			#file_name is a regex
			fn = common.subreg(url, file_name)
			if not fn:
				self.logger.warn( 'failed to parse file_name from url: %s', url)
				return None		
		else:
			#file_name is a fixed name
			fn = file_name
		if not common.subreg(fn, '(\.[a-z]{2,5}$)--is'):
			fn += '.'+format
		fn = prefix + fn

		if not os.path.exists(os.path.join(self.dir, dir)):
			os.makedirs(os.path.join(self.dir, dir))
		
		path = os.path.join(self.dir, dir, fn)

		if(os.path.exists(path)):
			return fn #already downloaded
		else:
			#start downloading the file
			options = common.combine_dicts(self.config, _options)		
			
			res = self.client.fetch_data(http.Request(url=url, bin = True, **options))	
					
			if res.status.code == 200 and res.data:
				common.put_bin(path, res.data)
				return fn
			else:
				return None


	

		




	def pagin(self, url, next=None, post=None,next_post=None, parse_list=None, detail= None, parse_detail= None, cc = None, max_pages = 0, debug=True, verify=None,  **_options):

		options = common.combine_dicts(self.config, _options)
		if not cc: 
			cc = self.config.get('cc', 1)
		
		queue = Queue()
		pages = [1]


		#apply scraper-level options
		
		threads = []	
 

		def handler(doc):
			doc.page = pages[0]
			if verify:				
				if not verify(common.DataObject(starturl=common.DataItem(url), page= pages[0], doc=doc)):
					doc.ok = False
					self.logger.warn("invalid doc at page {0}".format(pages[0]))
			
			
			self.logger.info('page %s', pages[0])
			
			
			#download and parse details	
			if detail:
				
				listings = detail(common.DataObject(starturl=common.DataItem(url), page= pages[0], doc=doc)) if hasattr(detail, '__call__') else doc.q(detail)
				
				self.logger.info('details: %s', len(listings) )

				for listing in listings:
					queue.put({'req':Request(url= listing if isinstance(listing, basestring) else listing.nodevalue(), **options) , 'cb': parse_detail})
					
			done = False

			_nexturl = None
			_next_post = None

			if next:
				_nexturl = next(common.DataObject(starturl=common.DataItem(url), page= pages[0], doc=doc)) if hasattr(next, '__call__') else ( next if next.startswith('http') else doc.x(next) )
			if next_post:
				if not next: 
					#next is not provided, use the original url
					_nexturl = doc.url								
				_next_post = next_post(common.DataObject(doc=doc, page=pages[0], starturl=common.DataItem(url))) if hasattr(next_post, '__call__') else next_post
			
			if next_post:
				if _next_post:
					done = False
				else:
					done = True
			else:
				if not _nexturl:
					done = True
				else:
					done = False				

			
			#if (next and _nexturl ) or (next_post and _next_post):
			if not done:
				
				#self.logger.debug('next_post: %s, _nexturl: %s', _next_post,  _nexturl)

				pages[0] += 1
				page = pages[0]

				if max_pages != 0 and page > max_pages:
					done = True
				else:	
					queue.put({'req':Request(_nexturl, _next_post, **options), 'cb': handler})
			else:
				done = True

			if done:
				#'tell worker pagin is done'
				for worker in threads:
					worker.done = True		


			if parse_list:
				parse_list(doc)

			
					

		##### end of the handler function ##################################################				

			
		#start workers		
		
		for i in range(cc):
			#print 'start threads'
			t = Worker(queue = queue, client= self.client, timeout=0.1)			
			t.setDaemon(True)
			threads.append(t)
			t.start()		

		#print url
		queue.put({'req':Request(url, post, **options), 'cb': handler})
		
		queue.join() #wait until this loop done	

		#waiting for all the threads exit
		try:
			while len(threads) > 0:
				time.sleep(0.01)
				#count = len(threads)
				for i, t in enumerate(threads):
					#t = threads[i]
					if not t.isAlive():
						del threads[i]
			
		except Exception as e:
			# print 'error while wating for threads stop'
			print e
			pass


	
        		
	def flush(self):
		if not hasattr(self, 'outdb'):
			#nothing to flush out
			return

		for filepath in self.outdb.keys():
			trackingobj = self.outdb.get(filepath)
			if trackingobj.format == 'csv':
				continue
			elif trackingobj.format == 'xls':
				import excellib
				excellib.save_xls(filepath, trackingobj.data)
			elif trackingobj.format == 'xlsx':
				import excellib
				excellib.save_xlsx(filepath, trackingobj.data)	

				
		#clear the db
		self.outdb = {}

	def save(self, record, file_name = 'result.csv', max=None, keys=[], id = None, headers = []):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
			
		path = os.path.join(self.dir, file_name)
		format = common.DataItem(path).subreg('\.([a-z]{2,5})$--is').lower()

		if not self.outdb.get(path):
			if os.path.exists(path):						
				os.remove(path)		
			self.outdb.update({ path: common.DataObject(cnt=0, data=[], ids = [], format = format)})	

		trackingobj = self.outdb.get(path)
		if keys or id:
			id = id or u"".join([ unicode( record[record.index(key) + 1 ] ) for key in keys])
			if id in trackingobj.ids:
				self.writingflag = False
				return
			else:
				trackingobj.ids.append(id)
		
		trackingobj.cnt += 1

		if format == 'csv':				
			#for csv format, save to file immediately	
			common.save_csv(path, record)
		elif format in ['xls', 'xlsx']:
			#save for later
			trackingobj.data.append(record)
		if max and trackingobj.cnt == max:
			self.flush() #save output files and quit
			os._exit(1)	

		#free the flag
		self.writingflag = False
	def append_line(self, file_name, line, dedup=False):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
		path = self.join_path(file_name)					

		if dedup:
			if not hasattr(self,'_data_lines'):				
				self._data_lines = []

			if common.md5(line) not in self._data_lines:								
				self._data_lines.append(common.md5(line))							
				common.append_file(path, line+'\r\n')
		else:
			common.append_file(path, line+'\r\n')
					

		#free the flag
		self.writingflag = False	

	def put_file(self, file_name, data):
		common.put_file(self.join_path(file_name), data)	
		return self

	def loop(self, url, next, post=None, cb=None, cc = 1, deep=2, debug=0, allow_external = False, link_filter=None,  **_options):
		options = common.combine_dicts(self.config, _options)

		doneurls = [common.md5(url)]
		queue = Queue()
		
		domain = common.get_domain(url).lower()



		def handler(doc):

			if doc.passdata.get('deep')<deep:
				for n in doc.q(next):
					nexturl = n.nodevalue()

					if domain != common.get_domain(nexturl):
						continue
					if link_filter and not link_filter(url=nexturl):
						continue

					if common.md5(nexturl) not in doneurls:					
						doneurls.append(common.md5(nexturl))
						queue.put({'req':Request(url=nexturl,passdata=dict(deep=doc.passdata.get('deep')+1), **options), 'cb': handler})					
			
			self.logger.debug( 'deep: %s', doc.passdata.get('deep') )
			self.logger.debug( doc.url )

			if cb:
				cb(doc)
		
		
		queue.put({'req':Request(url, post, passdata=dict(deep=1), **options), 'cb': handler})			
		#start workers					
		threads = []
		for i in range(cc if cc else self.config['cc']):
			t = Worker(queue = queue, client=self.client, timeout=0.01)
			t.setDaemon(True)
			threads.append(t)
			t.start()		

		
		queue.join() #wait until this loop done
		#waiting for all the threads exit
		try:
			while len(threads) > 0:
				time.sleep(0.1)
				#count = len(threads)
				for i, t in enumerate(threads):
					t = threads[i]
					if not t.isAlive():
						del threads[i]
			
		except Exception as e:
			print e	

	def find_emails(self, url):
		if not url: return []
		if not common.subreg(url, '^(http)'):
			url = 'http://'+url
		if '@' in url:
			return common.get_emails(url)	

		res = []		
		def link_filter(url):
			keywords = ["contact","about","info","imprint","kontakt","uber","wir","impressum","contacter","representatives"]
			for kw in keywords:
				if kw.lower() in url:
					return True
			return False		
		def parse(doc):
			for email in common.get_emails(doc.html()):
				if email not in res:
					res.append(email)

		self.loop(url=url,
			next="//a/@href | //iframe/@src",			
			deep=2,
			link_filter = link_filter,
			cb = parse,
			cc=10,
			debug=0

			)		
		return res		
			




