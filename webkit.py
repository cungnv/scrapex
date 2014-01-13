import sys
import signal
import sip
sip.setapi('QString', 2)
 
from optparse import OptionParser
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import *

import time

import common, http

app = QApplication(sys.argv)


class WebView(QWebView):
	def __init__(self, show = False, timeout=30, image=False, js=True, **options):				
		QWebView.__init__( self )
		self.timeout = timeout
		
		manager = NetworkAccessManager()		
		page = WebPage()
		page.setNetworkAccessManager(manager)
		self.setPage(page)
		
		self.setHtml('<html><body>Nothing</body></html>', QUrl('http://localhost'))

		self.loop = QEventLoop()
		self.timer = QTimer()
		self.timer.setSingleShot(True)
		self.timer.timeout.connect(self.loop.quit)	
		self.loadFinished.connect(self.loop.quit)

		#settings
		self.settings().setAttribute(QWebSettings.AutoLoadImages, image)
		self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
		self.settings().setAttribute(QWebSettings.JavascriptEnabled, js)


		if show: self.show()

		
	def open(self, url, show = False, **options):

		timeout = options.get('timeout', self.timeout)


		
		self.load(QUrl(url))

		self.timer.start(timeout* 1000)

		self.loop.exec_()

		#check for result
		if self.timer.isActive():
			#in time
			self.timer.stop()

		return self	
		
	def submit(self, css=None, **options):		
		timeout = options.get('timeout', self.timeout)

		if css is None:
			#submit the default form
			self.runjs('document.forms[0].submit()')
		else:	
			ele = self.findone(css)
			if not ele:
				raise Exception('no element match css:', css)				
			if ele.tagName().lower() == 'form':
				ele.evaluateJavaScript('this.submit()')
			else:				
				ele.evaluateJavaScript("var ev = document.createEvent('MouseEvents'); ev.initEvent('click', true, true); this.dispatchEvent(ev);")	

		self.timer.start(timeout * 1000)

		self.loop.exec_() #wait for result
		
		#done
		if self.timer.isActive():
			#in time
			self.timer.stop()

		return self	
	def click(self, css, text=None):
		eles = self.findall(css)
		if not eles:
			raise Exception('no element found to click:', css)
		target = None	
		if	text is not None:
			for ele in eles:
				if ele.toPlainText() == unicode(text):
					target = ele
					break
		else:
			target = eles[0]			
		
		target.evaluateJavaScript("var ev = document.createEvent('MouseEvents'); ev.initEvent('click', true, true); this.dispatchEvent(ev);")

		self.wait(1)	

		return self	

	def  waitfor(self, contain = None, **options):
		timeout = options.get('timeout', self.timeout)

		maxtime = time.time() + timeout
		while time.time() < maxtime:
			time.sleep(0)
			self.loop.processEvents()

			if contain and contain in self.html():	break

		return self		
	def wait(self, timeout):
		return self.waitfor(timeout=timeout)

	def fill(self, css, value):
		ele = self.findone(css)
		if not ele:
			raise Exception('no element found to fill:', css)
		if ele.tagName().lower() == 'input':				
			ele.evaluateJavaScript("this.value = '%s'" % value )
		else:
			ele.setPlainText(value)	

		return self
	def select(self, css, index=None, value=None, text=None):
		selecttag = self.findone(css)
		if not selecttag:
			raise Exception('no select tag found:', css)

		if selecttag.tagName().lower() == 'option':
			#select the option directly
			targetoption = selecttag
			selecttag = selecttag.parent()
			_index = -1
			for option in selecttag.findAll('option'):
				_index += 1
				if option.toPlainText() == targetoption.toPlainText():
					selecttag.evaluateJavaScript("this.selectedIndex = %s ;" % _index)
					break
			return self

			
		
		if index is not None:			
			selecttag.evaluateJavaScript("this.selectedIndex = %s ;" % index)
		elif value is not None:
			_index = -1
			for option in selecttag.findAll('option'):
				_index += 1
				if option.attribute('value') == str(value):
					selecttag.evaluateJavaScript("this.selectedIndex = %s ;" % _index)
					break
		elif text is not None:
			_index = -1
			for option in selecttag.findAll('option'):
				_index += 1
				if option.toPlainText() == unicode(text):
					selecttag.evaluateJavaScript("this.selectedIndex = %s ;" % _index)
					break		
		

		return self			

	def runjs(self, js):
		self.page().mainFrame().evaluateJavaScript(js)
		return self		

	def html(self):
		return unicode(self.page().mainFrame().toHtml())
	def doc(self):
		return	http.DOM(html = self.html(), url= self.url().toString())		

	def findall(self, css):
		return self.page().mainFrame().findAllElements(css).toList()	

	def findone(self, css):
		all = self.page().mainFrame().findAllElements(css).toList()
		return all[0] if all else None

	def __del__(self):					
		print 'closing...'
		self.setPage(None)


	def closeEvent(self, event):
		self.setPage(None)				
		self.loop.quit()
	
	def setProxy(self, hostport, userpass=None):
		self.page().networkAccessManager().setProxy(hostport, userpass)
		return self
		
		

class WebPage(QWebPage):	
	
    def javaScriptAlert(self, frame, message):
        print 'js alert: ', message

    def javaScriptConfirm(self, frame, message):
        return True

    def javaScriptPrompt(self, frame, message, default):
        print 'js prompt:%s%s' % (message, default)

    def javaScriptConsoleMessage(self, message, linenumber, sourceid):
        
        print 'console:%s%s%s' % (message, linenumber, sourceid)

    def shouldInterruptJavaScript(self):        
        return True	

class NetworkAccessManager(QNetworkAccessManager):
	def __init__(self):
		QNetworkAccessManager.__init__(self)		

	def setProxy(self, hostport, userpass=None):
		hostport = hostport.strip()

		host = hostport.split(':')[0]
		port = hostport.split(':')[1]

		user = userpass.split(':')[0] if userpass else None
		password = userpass.split(':')[1] if userpass else None

		proxy = QNetworkProxy(QNetworkProxy.HttpProxy, host, int(port), user, password)

		QNetworkProxy.setProxy(proxy)

		return self






		








	