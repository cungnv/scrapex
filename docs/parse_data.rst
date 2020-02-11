How to parse data in scrape
===========================
It's very easy to parse html document to data points in scrapex.

::

	>>> doc = s.load('https://github.com/search?q=scraping')
	>>> headline = doc.extract("//h3[contains(text(),'results')]").strip()
	>>> print(headline)
	59,371 repository results
	>>> 
	>>> number_of_results = headline.subreg('([\d\,]+)').replace(',','')
	>>> print(number_of_results)
	59371
	>>> 
	>>> next_page_url = doc.extract("//a[.='Next']/@href")
	>>> print(next_page_url)
	https://github.com/search?p=2&q=scraping&type=Repositories
	>>>
