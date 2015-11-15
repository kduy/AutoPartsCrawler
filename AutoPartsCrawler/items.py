# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class PartsItem(Item):
    #metadata
    modelYear = Field()
    make = Field()
    model = Field()
    trim = Field()
    section = Field()
    component = Field()
    price = Field()
