Code Samples
============
    


create scraper object
---------------------

::

    s = Scraper(
        dir = '.', #define the project directory, by default: use the current working directory
        use_cache = True, #enable the cache system
        use_cookie = True, #enable cookies
        delay = 0.1, # add 0.1 second delay between network requests
        retries = 2, #tries 2 more times if a http request failed
        log_file = 'log.txt', #enable default logging settings; set to None if you want to set logging yourself
        proxy_file = 'path/to/proxy.txt', #each line contains a proxy in host:port format
        proxy_auth = 'user:pass' # or None if no authentication required
    )


make http requests
------------------

::

    # GET request
    doc = s.load(url)

    # POST request
    doc = s.load(url, post = 'search_term=web+scraping&page=2')
    # or
    doc = s.load(url, post = {
        'search_term': 'web scraping',
        'page': '2'
        } )
    
    # just want html content, not creat the doc object

    html = s.load_html(url)

    # don't want to use cache in this request alone
    doc = s.load(url, use_cache = False)

    # don't want to use proxy and cookies in this request alone
    doc = s.load(url, use_cookie = False, use_proxy = False)    

    # use custom headers
    doc = s.load(url, headers={

        #copied from Google Chrome's Network Tab

        'Cookie': 'csrftoken=RcWB0BVsPfiRzvMQLHZ4WlmUbSLvVFKS; __utmt=1;', 
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Referer': 'http://scrapex.readthedocs.io/en/latest/features.html' 


    })

download files
--------------

::

    #download image file to folder images inside the project's directory
    s.download_file(image_url, filename = 'test.jpg', dir = 'images')

    #download a pdf file to somewhere else
    s.download_file(pdf_url, filename='/path/to/local/file.pdf')






