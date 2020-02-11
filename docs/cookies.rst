Working with session/cookies
============================
By default, session is turned off because it's a good practice for web scraping to avoid being tracked.

For scraping task that requires session to manage cookies, like scraping behind a loginwall, you can easily turn it on.
::


	>>> from scrapex import Scraper
	>>> s = Scraper(use_session=True)
	>>>
	>>> doc = s.load('http://httpbin.org/anything')
	>>> print('cookies sent:',doc.response.request.headers.get('Cookie'))
	cookies sent: None
	>>>
	>>> doc = s.load('http://httpbin.org/cookies/set?name1=value1&name2=value2')
	>>> doc = s.load('http://httpbin.org/anything')
	>>> print('cookies sent:',doc.response.request.headers.get('Cookie'))
	cookies sent: name1=value1; name2=value2
	>>> 


