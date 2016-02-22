import sys, os, json
from scrapex.core import Scraper
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
s = Scraper(use_cache=True, retries = 3, timeout=30, use_cookie=False)


def start():
	sites = {'Chevrolet':'http://www.chevyaccessories.com/', 'Buick':'http://www.buickaccessories.com/', 'GMC':'http://www.gmcaccessories.com/', 'Cadillac':'http://www.cadillacaccessories.com/'}
	for dv in sites:
		siteurl = sites[dv]
		
		for topcat in s.load(siteurl).q("//div[@id='vehicleNav']/ul/li"):
			topcategory = topcat.x("a").trim()
			print dv, topcategory
			for subcat in topcat.q("ul/li/img"):
				subcategory = subcat.x('@alt').trim()
				maxyear = subcat.x('@year')
				print '\t',subcategory
				firstdoc = s.load("{0}en-US/{1}/{2}/AjaxAccessories/".format(siteurl, subcat.x('@rel').replace(' ','%20'), maxyear))
				
				for yearnode in firstdoc.q("//li[.='MODEL YEAR']/following-sibling::li/a"):
					print '\t\t',yearnode.x('@year')
					for g1 in s.load("{0}en-US/{1}/{2}/AjaxAccessories/".format(siteurl, subcat.x('@rel').replace(' ','%20'), yearnode.x('@year'))).q("//div[starts-with(@class,'accListCol')]/div[@class='accCat']"):
						#print '\t\t\t',g1.x('p').trim()
						for g2 in g1.q("ul/li/a"):
							#print '\t\t\t\t',g2.nodevalue().trim()
							doc = s.load(g2.href().replace(' ','%20'))
							rs = doc.q("//tr[th[.='PART NO.']]/following-sibling::tr[td[@class='desc']]")
								
							cnt = 0
							for r in rs:
								cnt += 1
								itemno = r.x("td[2]").trim()
								imageurl = doc.x("//div[@class='accPicCol']/img[@class='accItem{0} accPic']/@src".format(cnt))
								res = [
									'Make', dv,
									'Vehicle Type', topcategory,									
									'Model', subcategory,
									'Year', yearnode.x('@year'),
									'Category', g1.x("p").trim(),
									'Subcategory', g2.nodevalue().trim(),
									'Part Name', r.x("td[@class='desc']").rr('\s+',' ').trim(),									
									'Part Number', itemno,
									'MSRP', r.x("td[3]").trim(),
									'Fitment', r.x("./following-sibling::tr[1]/td[@class='yearsCol']").rr('\s+',' ').trim(),
									'Image', s.save_link(imageurl, file_name='{0}.jpg'.format(itemno), dir='gm_images') if imageurl else ''

								]

								s.save(res, 'GM_result.csv')


if __name__ == '__main__':
	start()

