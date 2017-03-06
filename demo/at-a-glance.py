
from scrapex import Scraper, common

s = Scraper(dir = 'first-project', use_cache = True, show_status_message = False)

doc = s.load('https://www.yellowpages.com/search?search_terms=restaurant&geo_location_terms=New+York%2C+NY')

print doc.response.code

listings = doc.q("//div[@class='result']") #query result nodes by Xpath

print 'number of listings:', len(listings)

listing = listings[0] # just play with the first result node

name = listing.x(".//a[@class='business-name']").trim()

print name

phone = listing.x(".//*[@itemprop='telephone']").trim()

print phone

full_address = listing.q(".//p[@itemprop='address']/span").join(', ').replace(',,',',')

print full_address

parsed_address = common.parse_address(full_address)

print parsed_address

#save the record to csv file

s.save([
    #column name, value
    'name', name,
    'phone', phone,
    'address', parsed_address['address'],
    'city', parsed_address['city'],
    'state', parsed_address['state'],
    'zip code', parsed_address['zipcode']

    ], 'result.csv')
