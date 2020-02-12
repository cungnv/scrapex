
from scrapex import Scraper
from scrapex import common

s = Scraper()

def scrape_github_by_keyword(keyword):
	doc = s.load(url = 'https://github.com/search', params={'q': keyword})
	print(doc.extract("//h3[contains(text(),'results')]").strip())
	#....#

def scrape():
	keywords = ['scraping tool','python','nodejs','image processing','many more']
	print('start 3 threads')
	common.start_threads(keywords, scrape_github_by_keyword, cc=3)

if __name__ == '__main__':
	scrape()