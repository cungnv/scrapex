import http
import threading, random

class Worker(threading.Thread):	
	def __init__(self, queue, name=None, timeout = 5):

		threading.Thread.__init__(self)		
		self.queue = queue
		self.name = name if name else 'worker: '+ str(random.randint(1,1000))
		self.timeout = timeout		

	def run(self):
		try:
			while True:						
				item = self.queue.get(True, self.timeout)				
				try:										
					doc = http.open(item['req'])								
					if item['cb']:
						item['cb'](doc)						
				except Exception, e:
					print e						
				self.queue.task_done()
		except Exception, e2:
			#thread exited due to queue empty, nothing special
			#print 'exit thread'
			pass

