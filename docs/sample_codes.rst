Sample Codes
============
    


create scraper object
---------------------

::
    s = Scraper(
        dir = '.', #define the project directory, by default: use the current working directory
        use_cache = True, #enable the cache system
        use_cookie = True, #enable cookies
        delay = 0.1, # add 0.1 second delay between network requests
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
    doc = s.load(url, post = 'username=your+value&password=your+password')
    # or
    doc = s.load(url, post = {
        'username': 'your user',
        'password': 'your password'
        } )
    
    # just want html content, not creat the doc object

    html = s.load_html(url, post = 'username=your+value&password=your+password')

    



