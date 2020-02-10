
from scrapex import Scraper

s = Scraper(use_cache = True)

doc = s.load('https://github.com/search?q=scraping')

print(doc.extract("//title"))
print(doc.extract("//h3[contains(text(),'results')]").strip())

listings = doc.query("//ul[@class='repo-list']/li")

print('number of listings on first page:', len(listings) )

for listing in listings[0:3]:
	print('repo name: ',listing.extract(".//div[contains(@class,'text-normal')]/a"))