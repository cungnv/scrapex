Working with Proxies
====================
    
How to Enable Proxies
---------------------
The following setup will have the scraper select random proxy for each network request.
::

	>>> s = Scraper(
	...     proxy_file = '/path/to/proxy.txt',
	...		proxy_auth = 'username:password' # if authentication required
	
	)

Proxy File Format
-----------------
::

	host:port
	host:port
	...

Reload Proxy File
-----------------
::

	s.proxy_manager.load_proxies()

Create a Proxy object
---------------------
::

	>>> from scrapex.http import Proxy
	>>> proxy = Proxy(host, port, 'username:password')


Which proxy was selected?
-------------------------
::
	
	>>> doc = s.load(url)
	>>> proxy = doc.response.request.get('proxy')
	>>> print proxy.host, proxy.port


How to Stop Random Proxy Rotation?
----------------------------------
::

	>>> s.proxy_manager.sesssion_proxy = proxy #stay stick to this proxy only





