Custom HTTP Headers
=========================
By default, for each request, the scraper chooses a random User-Agent from a list of popular ones. It also uses a set of HTTP headers that a normal browser does.

You can easily customize the headers per request.
::


	>>> from scrapex import Scraper
	>>> s = Scraper()
	>>> doc = s.load('https://httpbin.org/headers')
	>>> print(doc.response.text)
	{
	  "headers": {
	    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
	    "Accept-Encoding": "gzip, deflate", 
	    "Accept-Language": "en-us,en;q=0.5", 
	    "Host": "httpbin.org", 
	    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0", 
	    "X-Amzn-Trace-Id": "Root=1-5e42957e-d5aa6cbae8ef6e0c2a2946c4"
	  }
	}
	>>>
	>>> headers={'User-Agent':'my own user-agent', 'Referer': 'some referer url'}
	>>> doc = s.load('https://httpbin.org/headers', headers=headers)
	>>> print(doc.response.text)
	{
	  "headers": {
	    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
	    "Accept-Encoding": "gzip, deflate", 
	    "Accept-Language": "en-us,en;q=0.5", 
	    "Host": "httpbin.org", 
	    "Referer": "some referer url", 
	    "User-Agent": "my own user-agent", 
	    "X-Amzn-Trace-Id": "Root=1-5e4295fe-d8454ea67c11ecf84e6c51be"
	  }
	}
	>>>







