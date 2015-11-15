import scrapy
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
import re
from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader
from scrapy.selector import Selector

from AutoPartsCrawler.items import PartsItem

class PartsCrawlSpider(CrawlSpider):
    name = 'parts_crawler'
    allowed_domain = ['https://www.parts.com/']
    start_urls = [
        'https://www.parts.com/index.cfm?fuseaction=store.sectionDiagram&siteid=2&vehicleid=412057&diagram=1381020&section=ELECTRICAL&Title=Audi-Q7-Premium-V6-3.0-%20Liter-GAS'
    ]

    def parse(self, response):
        #metadata = response.xpath('//*[@class="breadcrumb"]/li')
        # filename = response.url.split("/")[-2] + '.html'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        item = PartsItem()
        # item['modelYear'] = response.xpath('//*[@class="breadcrumb"]/li[2]/a/strong/text()').extract()[0]
        # item['make'] = response.xpath('//*[@class="breadcrumb"]/li[3]/a/strong/text()').extract()[0]
        # item['model'] = response.xpath('//*[@class="breadcrumb"]/li[4]/a/strong/text()').extract()[0]
        # item['trim'] = response.xpath('//*[@class="breadcrumb"]/li[5]/a/strong/text()').extract()[0]
        # item['component'] = response.xpath('//*[@class="breadcrumb"]/li[6]/text()').extract()[0]
        #
        # item['section'] = re.match(r'(.*)&section=(\w+)&(.*)', response.url).group(2)
        #
        # items = []
        # items.append(item)
        #return items

        l = ItemLoader(item=PartsItem(), response=response)

        l.add_xpath('modelYear', '//*[@class="breadcrumb"]/li[2]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('make', '//*[@class="breadcrumb"]/li[3]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('model', '//*[@class="breadcrumb"]/li[4]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('trim', '//*[@class="breadcrumb"]/li[5]/a/strong/text()', MapCompose(unicode.split), Join())
        l.add_xpath('component', '//*[@class="breadcrumb"]/li[6]/text()', MapCompose(unicode.strip))

        l.add_value('section',re.match(r'(.*)&section=(\w+)&(.*)', response.url).group(2) )

        # price
        components = Selector(response).xpath('//fieldset[@class="contentwaiting"]')
        groups = {}
        for component in components:
            lookupNo = component.xpath('section/dl[3]/dd/dfn/text()').re(r'(\d+)')
            price = component.xpath('section/dl[2]/dd[2]/del/text()').re(r'^\$(.*)')
            if not groups.has_key(lookupNo):
                groups[lookupNo] = price
                print lookupNo +"-"+ price


        return l.load_item()