import scrapy
from scrapy import Spider
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

from AutoPartsCrawler.items import PartsItem

class PartsCrawlSpider(CrawlSpider):
    name = 'parts_crawler'
    allowed_domain= ['parts.com']
    start_urls = (
        'https://www.parts.com/index.cfm?fuseaction=store.sectionDiagram&siteid=2&vehicleid=412057&diagram=1381384&section=ENGINE&Title=-'
    )

    def parse(self, response):
        metadata = response.xpath('//*[@class="breadcrumb"]/li')
