scrapex
=======

A simple web scraping lib for Python

#Required:
* Python 2.7
* lxml
* requests
* xlwt
* xlrd
* openpyxl

#Install

easy_install https://github.com/cungnv/scrapex/archive/master.zip

Or

pip install https://github.com/cungnv/scrapex/archive/master.zip

#Install Dependencies

easy_install requests

easy_install xlwt

easy_install xlrd

easy_install openpyxl

** Some notes for Windows users
- Download and install lxml from:
http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

- to use easy_install command, please download and run this python script:

	https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py

	...then make sure to add C:\Python27\Scripts to your system path
#How to Use
##Some important classes to know:
- Scraper: the main class to manage each scraping project, something like project directory, input/output, cache, cookies, making http requests, proxies, etc.
- Node: a wrap up around Lxmlnode object, to provide some convenient functions to query data from a node using xpath.
- DOM (extends Node): this one is normally created when the scraper loads a html page, -- all relative links within the page are resolved to absolute.
- DataItem (extens unicode): another convenient object to help manipulate a string easily, including extract data using regex.

##Code example:
Please checkout [sample project](https://github.com/cungnv/scrapex/blob/master/sample/gm.py)

```
from scrapex import core, common
#create a scraper object
s = Scraper(dir='c:/jobs/test')

#load a page
doc = s.load('https://www.google.com/search?q=scraping')

#result nodes
nodes = doc.q("//h3[@class='r']/a") #q for query
print 'nodes:', len(nodes)
for node in nodes:
	print 'title:', node.nodevalue().trim()
	print 'url:', node.x("href")


```








