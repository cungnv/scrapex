scrapex
=======

A simple web scraping lib for Python

#Install the framework:

- easy_install https://github.com/cungnv/scrapex/archive/master.zip
or
- pip install https://github.com/cungnv/scrapex/archive/master.zip

#Install dependencies:
- easy_install xlwt
- easy_install xlrd
- easy_install openpyxl

#Install lxml
- For windows: download and install lxml from http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

* Note: to use easy_install command, please download and run this python script:

	https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py

	...then make sure to add C:\Python27\Scripts to your system path (on Windows)

#How to Use

##Some important classes to know:
- Scraper: the main class to manage a scraping project. Something like project directory, input/output, cache, cookies, making http requests, proxies, etc.
- Node: a wrap up around Lxmlnode object, to provide some convenient functions to query data from a node using xpath.
- DOM (extends Node): this one is normally created when the scraper loads a html page, -- all relative links within the page are resolved to absolute.
- DataItem (extens unicode): another convenient object to help manipulate a string easily, including extract data using regex.

##Code example:
Please checkout [sample project](https://github.com/cungnv/scrapex/blob/master/sample/gm.py)

A simple usage
```
from scrapex import core, common
#create a scraper object
s = core.Scraper(dir='c:/jobs/test')

#load a page
doc = s.load('https://www.google.com/search?q=scraping')

#result nodes
nodes = doc.q("//h3[@class='r']/a") #q for query
print 'nodes:', len(nodes)
for node in nodes:
	res = [
	'title:', node.nodevalue().trim(),
	'url:', node.x("@href"),
	'domain:', node.x("@href").subreg('^https?://([^/]+)')
	]
	print res

	#save result to csv file
	s.save(res, 'result.csv')

```

Common use cases

```
# create a scraper with cookies, proxies enabled and cache disabled
s = core.Scraper(cache=False, cookie=True, proxyfile='proxy.txt', proxyauth='username:password')

# make a get request
doc = s.load(url)

# make a post request
doc = s.load(url, post="email=test%40gmail.com&pass=password") # or doc = s.load(url, post = {"email":test@gmail.com", "pass":"password"} )

# make a request with plain text result (instead of DOM object as result)
html = s.load(url)

# extract all required items from result page
listings = doc.q("//div[@id='results']//h3[@class='product-name']/a")
for node in listings:
	title = node.nodevalue().trim()
	detailurl = node.href() # or node.x("@href")
	

# extract some data point from html page
price = doc.x("//td[.='price:']/following-sibling::td").trim()

# extract id from url of current page
id = doc.url.subreg('/product/(\d+)/')


# save an image to disk
success = s.savelink(imageurl, dir = 'images', filename = common.DataItem(imageurl).subreg('/([^/]+)$') )


```








