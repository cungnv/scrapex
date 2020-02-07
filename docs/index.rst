.. scrapex documentation master file, created by
   sphinx-quickstart on Wed Feb 22 16:05:03 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to scrapex's documentation!
===================================

Scrapex is a simple Web Scraping Framework for Fast and Flexible Development. Works well on Python 2 and Python 3.

::

    Python 3.7.4 (v3.7.4:e09359112e, Jul  8 2019, 14:54:52)
    [Clang 6.0 (clang-600.0.57)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from scrapex import Scraper, common
    >>> from collections import OrderedDict
    >>> scraper = Scraper(use_cache=True)
    >>>
    >>> doc = scraper.load('https://www.yellowpages.com/search?search_terms=restaurant&geo_location_terms=New+York%2C+NY')
    >>> print(doc.response.status_code)
    200
    >>>
    >>> listings = doc.query("//div[@class='result']") #query result nodes by xpath
    >>> print('number of listings:', len(listings))
    number of listings: 30
    >>>
    >>> listing = listings[0] #let's play with the first result node
    >>>
    >>> item = OrderedDict() #to store data points
    >>>
    >>> item['name'] = listing.extract(".//a[@class='business-name']").strip()
    >>> print(item)
    OrderedDict([('name', Mr. K's)])
    >>>
    >>> item['phone'] = listing.extract(".//div[contains(@class,'phone')]").strip()
    >>> print(item['phone'])
    (212) 583-1668
    >>>
    >>> full_address = listing.query(".//p[@class='adr']/following-sibling::div").join(', ').replace(',,',',')
    >>> print(full_address)
    570 Lexington Ave, New York, NY 10022
    >>>
    >>> parsed_address = common.parse_address(full_address)
    >>> print(parsed_address)
    {'address': 570 Lexington Ave, 'city': New York, 'state': NY, 'zipcode': 10022}
    >>>
    >>> item['address'] = parsed_address['address']
    >>> item['city'] = parsed_address['city']
    >>> item['state'] = parsed_address['state']
    >>> item['zipcode'] = parsed_address['zipcode']
    >>>
    >>> print(item)
    OrderedDict([('name', Mr. K's), ('phone', (212) 583-1668), ('address', 570 Lexington Ave), ('city', New York), ('state', NY), ('zipcode', 10022)])
    >>>
    >>> scraper.save(item, 'output.csv') #save item to a csv file
    >>>
    >>> scraper.save(item, 'output.xlsx') #or save item to an excel file
    >>>




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
