import scrapy
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
import re
from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.http import Request
import locale
import urlparse

from AutoPartsCrawler.items import PartsItem

class PartsCrawlSpider(CrawlSpider):
    name = 'parts_crawler'
    allowed_domain = ['https://www.parts.com/']
    start_urls = [
        #'https://www.parts.com/index.cfm?fuseaction=store.sectionDiagram&siteid=2&vehicleid=412057&diagram=1381020&section=ELECTRICAL&Title=Audi-Q7-Premium-V6-3.0-%20Liter-GAS'
        #'https://www.parts.com/index.cfm'
        'https://www.parts.com/index.cfm?fuseaction=store.sectionSearch&storeid=2&vehicleid=412058&section=ENGINE&Title=Audi-Q7-Premium%20Plus-V6-3.0-GAS-OEM-Parts'
    ]

    def parse(self, response):

        allDiagramSelector = response.xpath('//div[@class="col-md-3 col-sm-3"]//div[@class="row"]//@href')
        if not allDiagramSelector:
            diagram_selector = response.xpath('//div[@class="sitem"]/div[@class="onethree-left"]//@href')
            for url in diagram_selector.extract():
                yield Request(url, callback=self.parse_item)
        else:
            section = re.match(r'(.*)&section=(\w+)&(.*)', response.url)
            if not section:
                section = "unknown"
            else:
                section = section.group(2)
            request = Request(allDiagramSelector.extract()[0], callback=self.parse_allDiagram)
            request.meta['section'] = section
            yield request


    def parse_allDiagram(self, response):
        diagramsSelector = response.xpath('//div[@class="item-image"]//@href')
        for url in diagramsSelector.extract():
            print url
            request = Request(url, callback=self.parse_item)
            request.meta['section'] = response.meta['section']
            yield request

    def parse_item(self, response):
        l = ItemLoader(item=PartsItem(), response=response)

        l.add_xpath('modelYear', '//*[@class="breadcrumb"]/li[2]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('make', '//*[@class="breadcrumb"]/li[3]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('model', '//*[@class="breadcrumb"]/li[4]/a/strong/text()', MapCompose(unicode.strip))
        l.add_xpath('trim', '//*[@class="breadcrumb"]/li[5]/a/strong/text()', MapCompose(unicode.split), Join())
        l.add_xpath('component', '//*[@class="breadcrumb"]/li[6]/text()', MapCompose(unicode.strip))

        section = re.match(r'(.*)&section=(\w+)&(.*)', response.url)
        if not section:
            section = response.meta['section']
        else:
            section = section.group(2)
        l.add_value('section',section)

        # price
        components = Selector(response).xpath('//fieldset[@class="contentwaiting"]')
        groups = {}
        for component in components:
            lookupNo = component.xpath('section/dl[3]/dd/dfn/text()').re(r'(\d+)')[0]
            price = component.xpath('section/dl[2]/dd[2]/del/text()').re(r'^\$(.*)')[0]
            if not groups.has_key(lookupNo):
                groups[lookupNo] = price

        totalPrice = 0.0
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        for key, value in groups.iteritems():
            totalPrice += locale.atof(value)

        l.add_value('price', totalPrice)
        return l.load_item()