

import sys
import os

from scrapex import Scraper
from scrapex import common

s = Scraper(use_cache=False, use_session=False, proxy_file='/var/scrape/proxy-lumus.txt')

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

def case2():
	doc = s.load('https://www.yellowpages.com/search?search_terms=restaurant&geo_location_terms=New+York%2C+NY')

	first_result = doc.node("//div[@class='result']")
	name = first_result.extract(".//a[@class='business-name']").strip()
	print(name)
	
	full_address = first_result.query(".//p[@class='adr']/following-sibling::div").join(', ').replace(',,',',')
	print(full_address)

	parsed_address = common.parse_address(full_address)
	print(parsed_address)

def case3():

	from collections import OrderedDict

	doc = s.load('https://github.com/search?q=scraping+framework')
	
	nodes = doc.query("//ul[@class='repo-list']/li")
	print('num of nodes:', len(nodes))
	
	for node in nodes:
		item = OrderedDict()
		item['name'] = node.extract(".//div[contains(@class,'text-normal')]/a")
		item['description'] = node.extract(".//div[@class='mt-n1']/p").strip()
		item['tags'] = node.query(".//a[contains(@class,'topic-tag')]").join(', ')

		s.save(item, 'results.csv')
		
		s.save(item, 'other_file.xlsx') #save this same item to another file

def case4():
	pass

		





if __name__ == '__main__':
	case3()