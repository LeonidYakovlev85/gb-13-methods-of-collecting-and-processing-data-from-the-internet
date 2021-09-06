"""
В items.py прописывается структура под собранные пауком данные.
Есть свойство, для которого указывается тип, это будет scrapy.Field(). Не нужно задумываться о том,
какого типа данные придут, необходимо только указать, какие поля будут поступать. Из items.py оформленная
структура попадает в pipeline.py, где происходит финальная обработка данных.
"""
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AvitoparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    name = scrapy.Field()
    photos = scrapy.Field()
    price = scrapy.Field()
    pass
