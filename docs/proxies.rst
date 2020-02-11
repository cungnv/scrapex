Working with proxies
====================
    
Enable proxies at scraper level, and choose a random one for each request
::
	
	>>> from scrapex import Scraper
	>>> s = Scraper(proxy_file="/path/to/a_proxy_file.txt")
	>>>
	>>> doc = s.load('https://httpbin.org/anything')
	>>> proxy_used = doc.response.json()['origin']
	>>> print(proxy_used)
	193.31.72.120
	>>>


Disable use of proxy at request level
::
	

	>>> doc = s.load('https://httpbin.org/anything', use_proxy=False)
	>>> client_real_ip = doc.response.json()['origin']
	>>> print(client_real_ip)
	42.114.13.13
	>>>

The format of proxy file without authentication
::
	
	ip:port
	ip:port
	ip:port
	.......

The format of proxy file with authentication
::
	
	user:password@ip:port
	user:password@ip:port
	user:password@ip:port
	.......

