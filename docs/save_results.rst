Save results to CSV/Excel files
===============================

::
	
	>>> from scrapex import Scraper
	>>> from collections import OrderedDict
	>>>
	>>> s = Scraper(use_cache=True)
	>>> doc = s.load('https://github.com/search?q=scraping+framework')
	>>> nodes = doc.query("//ul[@class='repo-list']/li")
	>>> print('num of nodes:', len(nodes))
	num of nodes: 10
	>>> 
	>>> for node in nodes:
	...     item = OrderedDict()
	...     item['name'] = node.extract(".//div[contains(@class,'text-normal')]/a")
	...     item['description'] = node.extract(".//div[@class='mt-n1']/p").strip()
	...     item['tags'] = node.query(".//a[contains(@class,'topic-tag')]").join(', ')
	...
	...     s.save(item, 'results.csv')
	...     s.save(item, 'other_file.xlsx') #save this same item to another file
	... 
	>>> 
