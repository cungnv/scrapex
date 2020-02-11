

import sys
import os

from scrapex import Scraper
from scrapex import common

s = Scraper(use_cache=False, use_session=False)

def case1():
	doc = s.load('https://github.com/search?q=scraping')
	headline = doc.extract("//h3[contains(text(),'results')]").strip()
	print(headline)

	number_of_results = headline.subreg('([\d\,]+)').replace(',','')
	print(number_of_results)

	next_page_url = doc.extract("//a[.='Next']/@href")
	print(next_page_url)

	





if __name__ == '__main__':
	case1()