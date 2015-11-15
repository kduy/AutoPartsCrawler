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
import logging


from AutoPartsCrawler.items import PartsItem


logger = logging.getLogger('PartsCrawlSpider')
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh.setFormatter(formatter)
logger.addHandler(fh)

class PartsCrawlSpider(CrawlSpider):



    name = 'parts_crawler'
    allowed_domain = ['https://www.parts.com/']
    start_urls = [
        #'https://www.parts.com/index.cfm?fuseaction=store.sectionDiagram&siteid=2&vehicleid=412057&diagram=1381020&section=ELECTRICAL&Title=Audi-Q7-Premium-V6-3.0-%20Liter-GAS'
        #'https://www.parts.com/index.cfm'
        #'https://www.parts.com/index.cfm?fuseaction=store.sectionSearch&storeid=2&vehicleid=412058&section=ENGINE&Title=Audi-Q7-Premium%20Plus-V6-3.0-GAS-OEM-Parts'
        #'https://www.parts.com/index.cfm?fuseaction=store.MakeSearch&VID=412058&MakeID=2&Make=Audi&ModelYear=2014&MODEL=Q7&Engine=V6-3.0-GAS'
        #'https://www.parts.com/index.cfm?fuseaction=store.MakeSearch&MakeID=2&Make=Audi-OEM-Parts&ModelYear=2014&MODEL=Q7'
        #'https://www.parts.com/index.cfm?fuseaction=store.MakeSearch&MakeID=2&ModelYear=2015&Make=Audi-OEM-Parts'
        #'https://www.parts.com/index.cfm?fuseaction=store.MakeSearch&MakeID=2&Title=Audi-OEM-Parts'
        'https://www.parts.com/index.cfm'
    ]

    def parse(self, response):
        allMakeSelector = response.xpath('//div[@class="item-image"]//@href')
        for url in allMakeSelector.extract():
            yield Request(url, callback=self.parse_make)

    def parse_make(self, response):
        allYearSelector = response.xpath('//div[@class="col-md-3 col-sm-4"]//@href')
        for url in allYearSelector.extract():
            yield Request(url, callback=self.parse_year)

    def parse_year(self, response):
        allModelSelector = response.xpath('//div[@class="col-md-3 col-sm-4"]//@href')
        for url in allModelSelector.extract():
            yield Request(url, callback=self.parse_model)

    def parse_model(self, response):
        allTrimSelector = response.xpath('//div[@class="col-md-3 col-sm-4"]//@href')
        for url in allTrimSelector.extract():
            yield Request(url, callback=self.parse_trim)

    def parse_trim(self, response):
        allSectionSelector = response.xpath('//div[@class="col-md-4 col-sm-3"]//@href')
        for url in allSectionSelector.extract():
            yield Request(url, callback=self.parse_section)


    def parse_section(self, response):
        allDiagramSelector = response.xpath('//div[@class="col-md-3 col-sm-3"]//div[@class="row"]//@href')
        if not allDiagramSelector:
            diagram_selector = response.xpath('//div[@class="sitem"]/div[@class="onethree-left"]//@href')
            for url in diagram_selector.extract():
                yield Request(url, callback=self.parse_item)
        else:
            section =re.match(r'(.*)&section=([\w|%20]+)(&(.*)|$)', response.url).group(2)
            request = Request(allDiagramSelector.extract()[0], callback=self.parse_allDiagram)
            request.meta['section'] = section
            yield request
        #todo: Group for https://www.parts.com/index.cfm?fuseaction=store.sectionSearch&storeid=2&vehicleid=412058&section=ELECTRICAL&Title=Audi-Q7-Premium%20Plus-V6-3.0-GAS-OEM-Parts
        #todo: replace %20 by space


    def parse_allDiagram(self, response):
        diagramsSelector = response.xpath('//div[@class="item-image"]//@href')
        for url in diagramsSelector.extract():
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

        section = re.match(r'(.*)&section=([\w|%20]+)(&(.*)|$)', response.url)
        if  section:
            section = section.group(2)
        else:
            try :
                section = response.meta['section']
            except Exception as ex:
                section = "unknown"
                logger.debug(response.url)


        l.add_value('section',section.replace("%20", " "))

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
        #todo: some parts are missing
        for key, value in groups.iteritems():
            totalPrice += locale.atof(value)

        l.add_value('price', totalPrice)
        return l.load_item()