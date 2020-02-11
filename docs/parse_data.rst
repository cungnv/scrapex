How to parse data in scrapex
===========================
It's very easy to parse html document to data points in scrapex.

parse data points from the document using XPATH
::

	>>> doc = s.load('https://github.com/search?q=scraping+framework')
	>>> headline = doc.extract("//h3[contains(text(),'results')]").strip()
	>>> print(headline)
	445 repository results
	>>> 
	>>> number_of_results = headline.subreg('([\d\,]+)').replace(',','')
	>>> print(number_of_results)
	445
	>>> 
	>>> next_page_url = doc.extract("//a[.='Next']/@href")
	>>> print(next_page_url)
	https://github.com/search?p=2&q=scraping+framework&type=Repositories
	>>>


parse data from a child node
::
	
	>>> nodes = doc.query("//ul[@class='repo-list']/li")
	>>> print('num of nodes:', len(nodes))
	num of nodes: 10
	>>> 
	>>> node = nodes[0] #play with first result
	>>> repo_name = node.extract(".//div[contains(@class,'text-normal')]/a")
	>>> print(repo_name)
	scrapy/scrapy
	>>>
	>>> description = node.extract(".//div[@class='mt-n1']/p").strip()
	>>> print(description)
	Scrapy, a fast high-level web crawling & scraping framework for Python.
	>>> 
	>>> tags = node.query(".//a[contains(@class,'topic-tag')]").join(', ')
	>>> print(tags)
	python, crawler, framework, scraping, crawling
	>>> 

parse street address components
::

	>>> from scrapex import common
	>>>
	>>> doc = s.load('https://www.yellowpages.com/search?search_terms=restaurant&geo_location_terms=New+York%2C+NY')
	>>> first_result = doc.node("//div[@class='result']")
	>>> 
	>>> name = first_result.extract(".//a[@class='business-name']").strip()
	>>> print(name)
	Mr. K's
	>>> 
	>>> full_address = first_result.query(".//p[@class='adr']/following-sibling::div").join(', ').replace(',,',',')
	>>> print(full_address)
	570 Lexington Ave, New York, NY 10022
	>>> 
	>>> parsed_address = common.parse_address(full_address)
	>>> print(parsed_address)
	{'address': 570 Lexington Ave, 'city': New York, 'state': NY, 'zipcode': 10022}
	>>> 


	

