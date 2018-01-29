import threading
import os
import random
import sys
import time
import json
import logging
import logging.config
import atexit
from Queue import Queue
from urlparse import urlparse

from scrapex.node import Node
from scrapex.worker import Worker
from scrapex.http import Request
from scrapex.cache import Cache
from scrapex import http, common, logging_config

logger = logging.getLogger(__name__)


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
			show_status_message = True,
			max_redirects = 3,
			
			use_default_logging = True,
			log_file = 'log.txt',
			log_post = False,
			log_headers = False
			
			)


		
		self.config.update(options)

		#expose important attributes
		self.dir = self.config.get('dir')
		if not os.path.exists(self.dir): os.makedirs(self.dir)		

		#load settings from local settings.txt
		if os.path.exists(self.join_path('settings.txt')):
			self.config.update(json.loads(common.get_file(self.join_path('settings.txt'))))

		
		#create cache object	
		cache_path = os.path.join(self.dir, self.config['cache_path'])	
		self.cache = Cache(cache_path)
	

		""" logging settings """

		if self.config['use_default_logging']:
			_log_file_path = self.join_path(self.config['log_file']) if self.config['log_file'] is not None else None

			# if _log_file_path:
			logging_config.set_default(log_file = _log_file_path, preserve = False)


		
		self.logger = logging.getLogger('scrapex')


		if self.config['show_status_message']:

			logger.info('start')
		
		atexit.register(self.__del__)

			
			
		self.proxy_manager = http.ProxyManager(proxy_file= self.join_path( self.config.get('proxy_file') ) if self.config.get('proxy_file') else None, proxy_auth=self.config.get('proxy_auth'))
		
		self.client = http.Client(scraper=self)

		#create an async downloader for this scraper
		self.downloader = Downloader(scraper=self, cc=3)
		
		#set flags
		self.writingflag = False

		#init the output db
		self.outdb = {}

		self._time_start = time.time()

	
	def get_log_stats(self):
		log_file = self.join_path(self.config['log_file']) if self.config['log_file'] is not None else None

		if log_file is None or not os.path.exists(log_file):
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
			log_file = self.join_path(self.config['log_file']) if self.config['log_file'] is not None else None
			
			if not log_file or self.config['parse_log'] is False:
				logger.info('Completed')
			else:
				logdata = common.parse_log(log_file)
				if logdata['errors'] == 0 and logdata['warnings'] == 0:
					logger.info('Completed successfully')
				else:
					logger.info('Completed with %s warning(s) and %s error(s)', logdata['warnings'], logdata['errors'])

			time_elapsed = round(time.time() - self._time_start, 2)

			minutes = round(time_elapsed/60) if time_elapsed > 60 else 0
			seconds = time_elapsed - minutes * 60
			
			if minutes:
				logger.info('time elapsed: %s minutes %s seconds', minutes, seconds)			
			else:	
				logger.info('time elapsed: %s seconds', seconds)			



	
	def join_path(self, filename):
		return os.path.join(self.dir, filename)
	def read_lines(self, filename):
		return common.read_lines(self.join_path(filename))	

	def write_json(self, filename, data):
		common.write_json(self.join_path(filename), data)
		return self
	def read_json(self, filename):
		return common.read_json(self.join_path(filename))

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
			
	def  save_link(self, url, filename, dir='images', **_options):
		""" backward supports """
		
		return self.download_file(url, filename, dir, **_options)

	def download_file(self, url, filename, dir='images', **_options):
		
		dir_path = self.join_path(dir)
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)

		path = os.path.join(self.dir, dir, filename)
		
		if(os.path.exists(path)):
			return filename #already downloaded
		else:
			#start downloading the file
			options = common.combine_dicts(self.config, _options)		
			
			res = self.client.fetch_data(http.Request(url=url, bin = True, **options))	
					
			if res.code == 200 and res.data:
				common.put_bin(path, res.data)
				return filename
			else:
				return None


	

	
        		
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

	def save(self, record, filename = 'result.csv', max=None, keys=[], id = None, headers = [], remove_existing_file = True, always_quoted=True):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
			
		path = os.path.join(self.dir, filename)
		format = common.DataItem(path).subreg('\.([a-z]{2,5})$--is').lower()

		if not self.outdb.get(path):
			if os.path.exists(path):
				if remove_existing_file:						
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
			common.save_csv(path, record, always_quoted=always_quoted)
		elif format in ['xls', 'xlsx']:
			#save for later
			trackingobj.data.append(record)
		if max and trackingobj.cnt == max:
			self.flush() #save output files and quit
			os._exit(1)	

		#free the flag
		self.writingflag = False
	def append_line(self, filename, line, dedup=False):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
		path = self.join_path(filename)					

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

	def put_file(self, filename, data):
		common.put_file(self.join_path(filename), data)	
		return self

	def read_csv(self, path, restype='list', encoding='utf8', line_sep='\r\n'):
		"""
		read a csv file into a list

		@restype: list or dict

		"""	
		res = []
		
		for r in common.read_csv(path=self.join_path(path),restype=restype, encoding=encoding, line_sep=line_sep):
			res.append(r)

		return res	



	def loop(self, url, next, post=None, cb=None, cc = 1, deep=2, debug=0, allow_external = False, link_filter=None, start_now=True,  **options):

		doneurls = [common.md5(url)]
		
		domain = common.get_domain(url).lower()



		def page_loaded(doc):

			if doc.req['meta']['deep']<deep:
				for n in doc.q(next):
					nexturl = n.nodevalue()

					if domain != common.get_domain(nexturl):
						continue
					if link_filter and not link_filter(url=nexturl):
						continue

					if common.md5(nexturl) not in doneurls:					
						doneurls.append(common.md5(nexturl))
						req = Request(url=nexturl, meta=dict(deep=doc.req['meta']['deep']+1),use_cache=True,  cb = page_loaded, **options)
						self.downloader.put(req)
			
			#allow the loop caller proccessing each loaded page			
			if cb:
				cb(doc)
		
		
		self.downloader.put(Request(url=url, post=post, meta=dict(deep=1), use_cache=True, cb = page_loaded, **options))			

		self.downloader.cc = cc
		if start_now:
			self.downloader.start()

	def find_emails(self, url, emails_dict, deep=2, link_filter=None):
		if not url: return []
		if not common.subreg(url, '^(http)'):
			url = 'http://'+url
		if '@' in url:
			return common.get_emails(url)	
		if url not in emails_dict:
			emails_dict[url] = []

		if not link_filter:		
			def link_filter(url):
				keywords = ["contact","about","agent","info","imprint","kontakt","uber","wir","impressum","contacter","representatives"]
				for kw in keywords:
					if kw.lower() in url:
						return True
				return False		

		def parse(doc):
			for email in common.get_emails(doc.html()):
				if email not in emails_dict[url]:
					emails_dict[url].append(email)

		self.loop(url=url,
			next="//a/@href | //iframe/@src",			
			deep=deep,
			link_filter = link_filter,
			cb = parse,
			cc=10,
			start_now = False

			)
	def mine_emails(self, url):
		""" 
		looks for emails on key pages of a website: homepage, contact

		"""
		if not url: return []
		if not common.subreg(url, '^(http)'):
			url = 'http://'+url
		if '@' in url:
			return common.get_emails(url)
		domain = common.get_domain(url)
		emails = []
		def _parse_emails(doc):
			link_texts = doc.q("//a").join(' | ')
			
			for email in common.get_emails(link_texts):
			
				if '@' in email and email not in emails:
					emails.append(email)

			if not emails:
				#try with text only, not links
				html = doc.remove("//script").html()
				for email in common.get_emails(html):
			
					if '@' in email and email not in emails:
						emails.append(email)

		
		homepage = self.load(url)
		_parse_emails(homepage)
		
		
		if emails:
			#no need to look on other page
			return emails		

		contact_url = homepage.x("//a[contains(@href,'contact') or contains(@href,'Contact')]/@href")

		if contact_url:
			contactpage = self.load(contact_url)
			_parse_emails(contactpage)
		

		return emails





	def pagin(self, url, next=None, post=None,next_post=None, parse_list=None, detail= None, parse_detail= None, cc = 3, max_pages = 0, list_pages_first=True, start_now=False, debug=True, verify=None, meta={},  **_options):
		
		if cc != self.downloader.cc:
			self.downloader.set_cc(cc)

		options = common.combine_dicts(self.config, _options)

		stats = common.DataObject(page=1)

		#apply scraper-level options

		def handler(doc):
			page = stats.page
			doc.page = page

			if verify:				
				if not verify(common.DataObject(starturl=common.DataItem(url), page= page, doc=doc)):
					doc.ok = False
					logger.warn("invalid doc at page {0}".format(page))
			
			logger.info('page %s', page)
			
			
			#download and parse details	
			if detail:
				
				listings = detail(common.DataObject(starturl=common.DataItem(url), page= page, doc=doc)) if hasattr(detail, '__call__') else doc.q(detail)
				
				logger.info('details: %s', len(listings) )

				for listing in listings:
					
					self.downloader.put(Request(url= listing if isinstance(listing, basestring) else listing.nodevalue(), cb = parse_detail, meta=meta, **options), onhold=list_pages_first)
					
			done = False

			_nexturl = None
			_next_post = None

			if next:
				_nexturl = next(common.DataObject(starturl=common.DataItem(url), page= page, doc=doc)) if hasattr(next, '__call__') else ( next if next.startswith('http') else doc.x(next) )
			if next_post:
				if not next: 
					#next is not provided, use the original url
					_nexturl = doc.url								
				_next_post = next_post(common.DataObject(doc=doc, page=page, starturl=common.DataItem(url))) if hasattr(next_post, '__call__') else next_post
			
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
				
				#logger.debug('next_post: %s, _nexturl: %s', _next_post,  _nexturl)

				stats.page += 1

				if max_pages != 0 and stats.page > max_pages:
					done = True
				else:	
					self.downloader.put(Request(_nexturl, _next_post, cb= handler, **options))
			else:
				done = True

			
			if parse_list:
				parse_list(doc)

			
					

		##### end of the handler function ##################################################				


		#start the initial url
		self.downloader.put(Request(url, post, cb= handler, **options))
		if start_now:
			self.downloader.start()
