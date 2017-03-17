Scrapex
=======
Scrapex is a Python Web Scraping Framework for Fast & Flexible Development.

Installation
============
::

    pip install https://github.com/cungnv/scrapex/archive/master.zip
    
.. note:: 

	You may need to `install Lxml`_ before install scrapex.

.. _install Lxml: http://lxml.de/installation.html

At a glance
===========
```python

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

```