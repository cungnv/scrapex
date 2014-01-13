from Queue import Queue
import threading, os, random, sys
from node import Node
from worker import Worker
from http import Request
import http
from cache import Cache
import common


import time, os
import urlparse
import requests


class Scraper(object):
	
	def __init__(self, **options):
		print 'start'
		self.onfinished = options.get('onfinished', None)

		_dir = os.path.dirname(sys.executable) if 'python' not in sys.executable.lower() else (os.getcwd())

		self.config = dict(
			dir = _dir, 
			cc = 1, 
			cache=True, 
			proxy=False, 
			proxyfile = os.path.join(_dir, 'proxy.txt'),  
			cookie = False,
			js=False, 
			jsentine = 'PyV8',
			timeout = 5,
			delay = 0.1,
			retries = 0

			)
		#auto enable/disable features based on user-passed options
		self.config.update(options)
		if(options.get('proxyfile') or options.get('proxyauth')):			
			if 'proxy' not in options: 
				self.config['proxy'] = True

		if not options.get('dir') and 'cache' not in options:
			self.config['cache'] = False	

		#expose important attributes
		self.dir = self.config.get('dir')
		if not os.path.exists(self.dir): os.makedirs(self.dir)			
		self.cache = Cache(os.path.join(self.dir, 'cache')) if self.config.get('cache') else None	
		self.client = requests.Session()		
		#self.client.config['keep_alive'] = False
		self.proxies = []
		self.loadproxies()

		#set flags
		self.writingflag = False
	def  __del__(self):
		if self.onfinished:
			self.onfinished()
		else:
			print 'done'	
	
	def joinpath(self, filename):
		return os.path.join(self.dir, filename)
	def readlines(self, filename):
		return common.readlines(self.joinpath(filename))	

	def clearcookie(self):
		self.client = requests.Session()
		return self

	def loadproxies(self):		
		proxyfile = self.config.get('proxyfile')		

		if proxyfile and self.config.get('proxy'):
			if not os.path.exists(proxyfile):
				raise Exception('proxyfile not found: {0}'.format(proxyfile))
			
			self.proxies = common.readlines(proxyfile)

		return self	

	def proxy(self):
		return self.proxies[random.randint(0, len(self.proxies)-1)]
	
	def load(self, url, post=None, **_options):		
		options = common.combinedicts(self.config, _options)		
		#apply scraper-level options
		options["client"] = (self.client if options.get('cookie')	else None)
		#print type(options["client"])
		if options.get('proxy') is True:
			options['proxy'] = self.proxy()
		if options.get('cache', False):
			options['cache'] = self.cache
		

		doc = http.open(Request(url = url, post = post, **options))
		return doc
	def savelink(self, url, dir='images', filename='auto', format='jpg', prefix='', **_options):
		fn = ''
		if filename == 'auto':			
			#special name
			fn = common.subreg(url, '/([^/\?\$]+\.[a-z]{2,4})$--is')			
			if not fn:
				print 'failed to parse filename from url: ', url
				return None
		elif not common.subreg(filename, '(\.[a-z]{2,4})$--is'):			
			#filename is a regex
			fn = common.subreg(url, filename)
			if not fn:
				print 'failed to parse filename from url: ', url
				return None		
		else:
			#filename is a fixed name
			fn = filename
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
			options = common.combinedicts(self.config, _options)		
			#apply scraper-level options
			options["client"] = (self.client if options.get('cookie')	else None)			
			if options.get('proxy') is True:
				options['proxy'] = self.proxy()
			bytes = http.open(http.Request(url=url, bin = True, **options))				
			if bytes:
				common.putbin(path, bytes)
				return fn
			else:
				return None


	def loop(self, url, next, post=None, cb=None, cc = None, **_options):
		options = common.combinedicts(self.config, _options)

		doneurls = [url]
		queue = Queue()



		#apply scraper-level options
		options["client"] = (self.client if options.get('cookie')	else None)
		if options.get('proxy') is True:
			options['proxy'] = self.proxy()
		
		if options.get('cache', False):
			options['cache'] = self.cache

 

		def handler(doc):
			if cb:
				cb(doc)

			for n in doc.q(next):
				nexturl = n.nodevalue()
				if nexturl not in doneurls:					
					doneurls.append(nexturl)
					queue.put({'req':Request(url=nexturl, **options), 'cb': handler})					
					
		#start workers					
		threads = []
		for i in range(cc if cc else self.config['cc']):
			t = Worker(queue = queue, timeout=0.01)
			t.setDaemon(True)
			threads.append(t)
			t.start()		

		queue.put({'req':Request(url, post, **options), 'cb': handler})

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

		




	def pagin(self, url, next=None, post=None,nextpost=None, parselist=None, detail= None, parsedetail= None, cc = None, maxpages = 0, debug=True,  **_options):

		options = common.combinedicts(self.config, _options)
		if not cc: 
			cc = self.config.get('cc', 1)
		
		queue = Queue()
		pages = [1]


		#apply scraper-level options
		options["client"] = (self.client if options.get('cookie')	else None)
		if options.get('proxy') is True:
			options['proxy'] = self.proxy()
		if options.get('cache', False):
			options['cache'] = self.cache

		threads = []	
 

		def handler(doc):
			
			if debug:
				print 'page ', pages[0]
			
			#download and parse details	
			if detail:
				if debug:
					print 'details: ', doc.q(detail).len()
				for listing in doc.q(detail):
					queue.put({'req':Request(url=listing.nodevalue(), **options) , 'cb': parsedetail})
					
			done = False

			_nexturl = None
			_nextpost = None

			if next:
				_nexturl = next(url=url, page= pages[0], doc=doc) if hasattr(next, '__call__') else doc.x(next)
			elif nextpost:
				_nexturl = doc.url				
				_nextpost = nextpost(doc) if hasattr(nextpost, '__call__') else nextpost
			
			if (next and _nexturl) or (nextpost and _nextpost):
				#print _nexturl

				pages[0] += 1
				page = pages[0]

				if maxpages != 0 and page > maxpages:
					done = True
				else:	
					queue.put({'req':Request(_nexturl, _nextpost, **options), 'cb': handler})
			else:
				done = True

			if done:
				#'tell worker pagin is done'
				for worker in threads:
					worker.done = True		


			if parselist:
				parselist(doc)

			# if next:		
			# 	#go to the next page				
			# 	nexturl = next(url=url, page= pages[0], doc=doc) if hasattr(next, '__call__') else doc.x(next)
			# 	#print nexturl
			# 	#del doc #release memory

			# 	if nexturl:				
			# 		pages[0] += 1
			# 		page = pages[0]
			# 		if maxpages != 0 and page > maxpages:
			# 			#max allowed page reached
			# 			return
					
			# 		queue.put({'req':Request(url=nexturl, **options), 'cb': handler})	

			# elif nextpost:
			# 	nexturl = doc.url
			# 	#print nexturl
			# 	post = nextpost(doc) if hasattr(nextpost, '__call__') else nextpost

			# 	if post:
			# 		pages[0] += 1
			# 		page = pages[0]
			# 		if maxpages != 0 and page > maxpages:
			# 			#max allowed page reached
			# 			return
			# 		queue.put({'req':Request(nexturl, post, **options), 'cb': handler})
			# else:
			# 	#no next page, so tell all workers the pagin is done
			# 	print 'tell worker pagin is done'
			# 	for worker in threads:
			# 		worker.done = True				
					

		##### end of the handler function ##################################################				

			
		#start workers		
		
		for i in range(cc):
			#print 'start threads'
			t = Worker(queue = queue, timeout=0.1)			
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


	def loadbatch(self, urlfile, filenamereg= None, urlreg=None, makefilename =None,  cb= None, cc = 1, debug=True,  **_options):

		options = common.combinedicts(self.config, _options)
		isproxy = options.get('proxy') == True
		
		if not cc: 
			cc = self.config.get('cc', 1)
		
		queue = Queue()
		
		#apply scraper-level options
		options["client"] = (self.client if options.get('cookie')	else None)
		
		if options.get('cache', False):
			options['cache'] = self.cache
		
		
		urls = common.readlines(os.path.join(self.dir, urlfile))
		if debug: print 'urls:', len(urls)	
		for line in urls:			
			options['proxy'] = self.proxy() if isproxy else None

			url = common.subreg(line, urlreg) if urlreg else line
			filename = common.subreg(line, filenamereg) if filenamereg else (makefilename(line) if makefilename  else common.md5(url) + '.htm')
			
			queue.put({'req':Request(url = url, filename=filename, **options), 'cb': cb})

		#start workers		
		threads = []
		for i in range(cc):
			t = Worker(queue = queue, timeout=5)
			t.done = True
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
		


	def downloadfiles(self, urlfile, dir, urlreg=None, filenamereg=None, cb= None, cc = 1, debug=True,  **_options):
		def makecb(fullpath):
			def savefile(data):
				return common.putbin(fullpath, data)
			return savefile	

		options = common.combinedicts(self.config, _options)

		isproxy = _options.get('proxy', False)
		
		if not cc: 
			cc = self.config.get('cc', 1)
		
		queue = Queue()
		
		#apply scraper-level options
		options["client"] = (self.client if options.get('cookie')	else None)
		
		if options.get('cache', False):
			options['cache'] = self.cache
		#start workers			
		threads = []
		for i in range(cc):
			t = Worker(queue = queue, timeout=100)
			t.setDaemon(True)
			threads.append(t)
			t.start()
		lines = common.readlines(os.path.join(self.dir, urlfile))
		if debug: print 'urls:', len(lines)
		files = []	
		for line in lines:			
			options['proxy'] = self.proxy() if isproxy else None
			options['bin'] = True
			url = line if not urlreg else common.subreg(line, urlreg)
			filename = common.subreg(line, filenamereg) if filenamereg else common.filename(url)
			fullpath = os.path.join(self.dir, dir, filename)		
			if(os.path.exists(fullpath)): continue
			if filename in files:
				continue
			else:
				files.append(filename)	

			funcsavefile = makecb(fullpath)
			
			queue.put({'req':Request(url = url, **options), 'cb': funcsavefile})
		if debug:
			print 'unique files:', len(files)	

		queue.join() #wait until this loop done		
		#waiting for all the threads exit
		try:
			while len(threads) > 0:
				time.sleep(0.1)
				#count = len(threads)
				for i,t in enumerate(threads):
					t = threads[i]
					if not t.isAlive():
						del threads[i]
			
		except Exception as e:
			print e
        		

	def save(self, record, filename = 'result.csv'):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
			
		path = os.path.join(self.dir, filename)
		if not hasattr(self, path) and os.path.exists(path):						
			os.remove(path)
			setattr(self, path, '')	
					
		
		#start writing
		common.savecsv(path, record)
		#free the flag
		self.writingflag = False
	def appendline(self, filename, line, dedup=False):		
		#waiting while other thread writing
		while self.writingflag:			
			pass
		#hold the flag	
		self.writingflag = True
		path = self.joinpath(filename)					

		if dedup:
			if not hasattr(self,'_data_lines'):				
				self._data_lines = []

			if common.md5(line) not in self._data_lines:								
				self._data_lines.append(common.md5(line))							
				common.appendfile(path, line+'\r\n')
		else:
			common.appendfile(path, line+'\r\n')
					

		#free the flag
		self.writingflag = False	

	def putfile(self, filename, data):
		common.putfile(self.joinpath(filename), data)	
		return self

