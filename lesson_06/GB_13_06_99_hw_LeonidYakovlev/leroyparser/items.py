"""
В items.py прописывается структура под собранные пауком данные.
Есть свойство, для которого указывается тип, это будет scrapy.Field().
Не важно, какого типа данные придут, необходимо только указать, какие поля будут поступать.
Из items.py оформленная структура попадает в pipeline.py, где происходит финальная обработка данных.
"""
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, MapCompose


def get_id(response_url):
    # response_url имеет вид «https://leroymerlin.ru/.../product-name-123456789/»
    # Разбиение поступившего response.url по «-»; удаление «/»; остаётся только числовой фрагмент
    _id = response_url.split('-')[-1].replace('/', '')
    return _id


def clean_parameter_value(parameter_value):
    # parameter_value имеет вид «     some_value     »
    # Удаление пробелов в начале и конце строки
    parameter_value = parameter_value.strip()
    # Если parameter_value имеет числовое значение, то сделать его float, иначе вернуть текущее значение
    try:
        return float(parameter_value)
    except ValueError:
        return parameter_value


def change_price_type(price):
    price = float(price)
    return price


class LeroyparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field(input_processor=MapCompose(get_id), output_processor=TakeFirst())
    link = scrapy.Field(output_processor=TakeFirst())
    name = scrapy.Field(output_processor=TakeFirst())
    parameter_name = scrapy.Field()
    parameter_value = scrapy.Field(input_processor=MapCompose(clean_parameter_value))
    # Наполнение parameters данными из parameter_name и parameter_value происходит в pipelines.py
    parameters = scrapy.Field()
    price = scrapy.Field(input_processor=MapCompose(change_price_type), output_processor=TakeFirst())
    images = scrapy.Field()
