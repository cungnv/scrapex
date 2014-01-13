import http
import threading, random, signal

class Worker(threading.Thread):	
	def __init__(self, queue, name=None, timeout = 5):

		threading.Thread.__init__(self)		
		self.queue = queue
		self.name = name if name else 'worker: '+ str(random.randint(1,1000))
		self.timeout = timeout
		self.done = False		

	def run(self):
		try:
			while True:					
				if not self.done:
					item = self.queue.get(True, 1) # wait 1 second before die
				else:
					item = self.queue.get(True, self.timeout) # don't wait forever, 				
				try:										
					doc = http.open(item['req'])								
					if item['cb']:
						item['cb'](doc)						
				except Exception, e:
					print e						
				self.queue.task_done()
		except Exception, e2:
			#thread exited due to queue empty, nothing special
			#print 'worker exit'
			pass

