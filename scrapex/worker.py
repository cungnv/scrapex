from builtins import str
import threading, random, logging
from scrapex import http


class Worker(threading.Thread):	
	def __init__(self, queue, client, name=None, timeout = 5):

		threading.Thread.__init__(self)		
		self.queue = queue
		self.name = name if name else 'worker: '+ str(random.randint(1,1000))
		self.timeout = timeout
		self.done = False		
		self.client = client

	def run(self):
		logger = logging.getLogger(__name__)
		try:
			while True:					
				if not self.done:
					item = self.queue.get(True, 1) # wait 1 second before die
				else:
					item = self.queue.get(True, self.timeout) # don't wait forever, 				
				try:										
					doc = self.client.load(item['req'])								
					if item['cb']:
						item['cb'](doc)						
				except Exception as e:
					logger.exception(e)

				self.queue.task_done()
		except Exception as e2:
			#thread exited due to queue empty, nothing special		
			pass
			

