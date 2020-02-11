

import sys
import os

from scrapex import Scraper
from scrapex import common

s = Scraper(use_cache=False, use_session=False)

def case1():
	doc = s.load('https://github.com/search?q=scraping+framework')
	headline = doc.extract("//h3[contains(text(),'results')]").strip()
	print(headline)

	number_of_results = headline.subreg('([\d\,]+)').replace(',','')
	print(number_of_results)

	next_page_url = doc.extract("//a[.='Next']/@href")
	print(next_page_url)

	nodes = doc.query("//ul[@class='repo-list']/li")
	print('num of nodes:', len(nodes))
	
	node = nodes[0] #play with first result

	repo_name = node.extract(".//div[contains(@class,'text-normal')]/a")
	print(repo_name)

	description = node.extract(".//div[@class='mt-n1']/p").strip()
	print(description)
	
	tags = node.query(".//a[contains(@class,'topic-tag')]").join(', ')
	print(tags)






if __name__ == '__main__':
	case1()