.. scrapex documentation master file, created by
   sphinx-quickstart on Wed Feb 22 16:05:03 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to scrapex's documentation!
===================================

Scrapex is a simple web scraping framework. Built on top of `requests <https://github.com/psf/requests>`_ and `lxml <https://lxml.de/>`_, supports Python 2 and Python 3.



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


Key Features
============

    .. include:: inc.features.txt




.. toctree::
    :maxdepth: 2

    installation
    example_script
    make_requests
    parse_data
    save_results
    proxies
    headers
    cookies
    download_files
    cache
    multi_threads

    
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
