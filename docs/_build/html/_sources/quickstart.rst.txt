Quick Start
============

Create a very basic scraper to scrape github search result page:

::

    from scrapex import Scraper

    #create a scraper, the central object
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
    
    logger = s.logger

    #load a page
    doc = s.load('https://github.com/search?q=python+web+scraping&type=Repositories&ref=searchresults')

    #extract the headline using xpath
    headline = doc.x("//h3[contains(text(), 'result')]").trim()
    logger.info(headline)

    #extract the result count from the headline using regex
    logger.info('result count: %s', headline.subreg('([\d\,]+)')) 

    #select all result nodes. q means query
    rs = doc.q("//ul[@class='repo-list js-repo-list']/li") 
    logger.info('# of listings on first page: %s', len(rs))

    #loop through each result, and save details to a csv file
    for r in rs:
        s.save([
            # a list of name,value pairs.
            # the names will become the csv's column names

            'title', r.x(".//h3"),
            'url', r.x(".//h3/a/@href"),
            'short description', r.x("p"),

            #firstly query all the tag links INSIDE this r node, then join the link text by a comma
            'tags', r.q("div/a[contains(@class, 'topic-tag')]").join(', ')

            ],

            #the csv filename, located inside the project's directory
            'result.csv' 

            )


==> The console screen:

::
    
    INFO: start
    INFO: We’ve found 763 repository results
    INFO: result count: 763
    INFO: # of listings on first page: 10
    INFO: Completed successfully
    INFO: time elapsed: 0.0 minutes 0.17 seconds
    






