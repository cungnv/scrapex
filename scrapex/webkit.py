
import sys, time, signal, sip, random

# sip.setapi('QString', 2)
 
from optparse import OptionParser
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import *
from PyQt4.QtCore import QUrl

#prevent qt messages from the Terminal screen
from PyQt4.QtCore import qInstallMsgHandler
from PyQt4.Qt import QtMsgType


def myQtMsgHandler( msg_type, msg_string ) :
	pass

qInstallMsgHandler(myQtMsgHandler)
	

from scrapex import common, http, agent



app = QApplication(sys.argv)



class WebView(QWebView):
	def __init__(self, show = False, timeout=30, image=False, js=True, **options):				
		

		QWebView.__init__( self )
		self.timeout = timeout
		
		proxy = options.get('proxy')
		proxyauth = options.get('proxyauth')

		manager = NetworkAccessManager()
		if proxy:
			manager.setProxy(proxy, proxyauth)	

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

		
	def open(self, url, **options):

		timeout = options.get('timeout', self.timeout)
		if isinstance(url, QUrl):
			self.load(url)
		else:
			self.load(QUrl(url))
			
		

		self.timer.start(timeout* 1000)

		self.loop.exec_()

		#check for result
		if self.timer.isActive():
			#in time
			self.timer.stop()

		return self	
		
	def getcookies(self, url=None):

		cookies = []
		
		for cookie in self.page().networkAccessManager().cookieJar().cookiesForUrl(QUrl(url)):

			# _domain = cookie.domain()
			# if domain and domain.lower() not in _domain:
			# 	continue
			cookies.append('%s=%s' % (cookie.name(), cookie.value()))
		return '; '.join(cookies)

	def clear_cookies(self):
		self.page().networkAccessManager().setCookieJar(QNetworkCookieJar())
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
				if unicode(ele.toPlainText()).strip().lower() == unicode(text).lower():
					target = ele
					break
		else:
			target = eles[0]			
		if not target:
			print 'failed to click: the target object not fould'

		#print dir(target)	
		if target.hasAttribute('target'):
			target.setAttribute('target','')
		
		# print target.toOuterXml()
		
		target.evaluateJavaScript("var ev = document.createEvent('MouseEvents'); ev.initEvent('click123', true, true); this.dispatchEvent(ev);")


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

	def fill(self, css, value, append=False):
		ele = self.findone(css)
		if not ele:
			raise Exception('no element found to fill:', css)
		if unicode(ele.tagName()).lower() in ['input', 'option']:				
			if not append:
				ele.evaluateJavaScript("this.value = '%s'" % value )
			else:
				ele.evaluateJavaScript("this.value = this.value + '%s'" % value )	
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
		return	http.Doc(html = self.html(), url= self.url().toString(), status = http.Status(code=200, error=None, final_url=self.url().toString()))

	def findall(self, css):
		return self.page().mainFrame().findAllElements(css).toList()	

	def findone(self, css):
		all = self.page().mainFrame().findAllElements(css).toList()
		return all[0] if all else None

	def __del__(self):					
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
		pass
		# print 'console:%s%s%s' % (message, linenumber, sourceid)

	def shouldInterruptJavaScript(self):        
		return True	

	def userAgentForUrl(self, url):
		all_agents = [agent.firefox, agent.chrome]
		useragent = random.choice(all_agents)
		return useragent
	

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
		# print 'set application proxy...'
		# QNetworkAccessManager.setProxy(self, proxy)
		QNetworkProxy.setApplicationProxy(proxy) #to let https requests use proxy

		return self

	# def createRequest(self, operation, request, data):
	# 	""" testing """	
	# 	# print 'making request...'
	# 	# print dir(request)

	# 	request = QNetworkAccessManager.createRequest(self, operation, request, data)

	# 	header = request.header(QNetworkRequest.LocationHeader)
	# 	#apply ssl protocol
	# 	# sslconf = QSslConfiguration.defaultConfiguration()
	# 	# sslconf.setProtocol(QSsl.TlsV1)
	# 	# request.setSslConfiguration(sslconf)

	# 	# print dir(request)

	# 	return request







		








	
