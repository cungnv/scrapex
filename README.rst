
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

Copyright (c) 2020 Cung Nguyen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
