Working with Cache System
=========================
By default, cache is turned off. In many scraping jobs, we need to make some tweaks to our parsing part and re-scrape the site again. In that situation, caching the html content from the first scrape is very helpful, especially for big scrapes.

Turn on the cache.
::
	
	>>> import os
	>>> from scrapex import Scraper
	>>> s = Scraper(use_cache=True)
	>>> doc = s.load('http://httpbin.org/anything')
	>>>
	>>> print(os.listdir(s.cache.location))
	['47a7ec08a34ed1fb8c78c931818dd082.htm']
	>>>

Disable cache at request level
::


	>>> doc = s.load('http://httpbin.org/anything', use_cache=False)

