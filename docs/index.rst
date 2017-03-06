.. scrapex documentation master file, created by
   sphinx-quickstart on Wed Feb 22 16:05:03 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to scrapex's documentation!
===================================

Scrapex is a Python Web Scraping Framework for Fast & Flexible Development.

At a glance:
::

    >>> from scrapex import Scraper, common
    >>> 
    >>> s = Scraper(dir = 'first-project', use_cache = True)
    >>> 
    >>> doc = s.load('https://www.yellowpages.com/search?search_terms=restaurant&geo_location_terms=New+York%2C+NY')
    >>> 
    >>> print doc.response.code
    200
    >>> 
    >>> listings = doc.q("//div[@class='result']") #query result nodes by Xpath
    >>> 
    >>> print 'number of listings:', len(listings)
    number of listings: 30
    >>> 
    >>> listing = listings[0] # just play with the first result node
    >>> 
    >>> name = listing.x(".//a[@class='business-name']").trim()
    >>> 
    >>> print name
    Mr. K's
    >>> 
    >>> phone = listing.x(".//*[@itemprop='telephone']").trim()
    >>> 
    >>> print phone
    (212) 583-1668
    >>> 
    >>> full_address = listing.q(".//p[@itemprop='address']/span").join(', ').replace(',,',',')
    >>> 
    >>> print full_address
    570 Lexington Ave, New York, NY, 10022
    >>> 
    >>> parsed_address = common.parse_address(full_address)
    >>> 
    >>> print parsed_address
    {'city': u'New York', 'state': u'NY', 'zipcode': u'10022', 'address': u'570 Lexington Ave'}
    >>> 
    >>> #save the record to csv file
    ... 
    >>> s.save([
    ...     #column name, value
    ...     'name', name,
    ...     'phone', phone,
    ...     'address', parsed_address['address'],
    ...     'city', parsed_address['city'],
    ...     'state', parsed_address['state'],
    ...     'zip code', parsed_address['zipcode']
    ... 
    ...     ], 'result.csv')
    >>> 


source code:
::

    .. include:: ../demo/at-a-glance.py





.. toctree::
    :maxdepth: 2

    quickstart
    installation
    features
    code_samples
    data_extraction
    parse_address
    proxies
    cookies
    headers
    logging_debugging
    dataitem
    cache
    scrapex_selenium
    other_usages
    
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
