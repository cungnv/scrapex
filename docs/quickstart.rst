Quick Start
============
    
.. code-block:: python


    from scrapex import Scraper

    s = Scraper(
        
        dir = '.', #define the project directory

        use_cache = True, #enable the cache system

        use_cookie = True, #enable cookies

        delay = 1, # add 1 second delay between network requests

        log_file = 'log.txt', #enable default logging settings


    )

    logger = s.logger

    #load a page

    doc = s.load('https://github.com/search?q=python+web+scraping&type=Repositories&ref=searchresults')

    #extract the headline using xpath
    headline = doc.x("//h3[contains(text(), 'result')]").trim()

    logger.info(headline)

    #extract the result count from the headline using regex

    logger.info('result count: %s', headline.subreg('([\d\,]+)')) 

    #loop through each result of the first result page

    rs = doc.q("//ul[@class='repo-list js-repo-list']/li") # q stands for query, select nodes by xpath

    logger.info('# of listings on first page: %s', len(rs))

    for r in rs:

        #save record to a csv file
        s.save(
            #a list of name,value pairs.
            #the names will become the csv's column names

            [

            'title', r.x(".//h3"),
            
            'url', r.x(".//h3/a/@href"),


            'short description', r.x("p"),

            #firstly query all the tag links INSIDE this r node, then join the link text by a comma
            'tags', r.q("div/a[contains(@class, 'topic-tag')]").join(', ')

            ],

            'result.csv' #the csv filename, located inside the product's directory

            )

