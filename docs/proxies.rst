Working with Proxies
====================
    
Enable proxies at scraper level, and choose a random one for each request
::
	
	>>> from scrapex import Scraper
	>>> s = Scraper(proxy_file="/var/scrape/proxy.txt")
	>>>
	>>> doc = s.load('https://httpbin.org/anything')
	>>> proxy_used = doc.response.json()['origin']
	>>> print(proxy_used)
	193.31.72.120
	>>>


Disable use of proxies at request level
::
	

	>>> doc = s.load('https://httpbin.org/anything', use_proxy=False)
	>>> client_real_ip = doc.response.json()['origin']
	>>> print(client_real_ip)
	42.114.13.13
	>>>

The format of proxies file without authentication
::
	
	ip:host
	ip:host
	ip:host
	.......

The format of proxies file with authentication
::
	
	user:password@ip:host
	user:password@ip:host
	user:password@ip:host
	.......

