
Scrapex is a simple web scraping framework. Built on top of `requests <https://github.com/psf/requests>`_ and `lxml <https://lxml.de/>`_, supports Python 2 and Python 3.


Installation
============
To install stable version
::

    pip install scrapex

To install development version
::
            
    pip install https://github.com/cungnv/scrapex/archive/master.zip
    
Quick start
===========
::
    
    
    >>> from scrapex import Scraper
    >>> s = Scraper(use_cache = True)
    >>> doc = s.load('https://github.com/search?q=scraping')
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

Documentation available at `scrapex.readthedocs.io <https://scrapex.readthedocs.io/>`_.

LICENSE
=======
    .. include:: LICENSE