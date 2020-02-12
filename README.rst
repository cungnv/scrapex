Scrapex
=======
Scrapex is a simple web scraping framework. Built on top of `requests <https://github.com/psf/requests>` and `lxml <https://lxml.de/>`, supports both Python 2 and Python 3. `Documentations <https://scrapex.readthedocs.io/>`.

To install stable version, use this command in your terminal:
::

    pip install scrapex

To install development version, use this command in your terminal:
::
            
    pip install https://github.com/cungnv/scrapex/archive/master.zip
    

::
    
    
    >>> from scrapex import Scraper
    >>> s = Scraper(use_cache = True)
    >>> doc = s.load('https://github.com/search?q=scraping')
    >>> 
    >>> print(doc.extract("//title"))
    Search · scraping · GitHub
    >>> 
    >>> print(doc.extract("//h3[contains(text(),'results')]").strip())
    59,256 repository results
    >>> 
    >>> listings = doc.query("//ul[@class='repo-list']/li")
    >>> print('number of listings on first page:', len(listings) )
    number of listings on first page: 10
    >>> 
    >>> for listing in listings[0:3]:
    ...     print('repo name: ',listing.extract(".//div[contains(@class,'text-normal')]/a"))
    ... 
    repo name:  scrapinghub/portia
    repo name:  scrapy/scrapy
    repo name:  REMitchell/python-scraping
    >>> 

