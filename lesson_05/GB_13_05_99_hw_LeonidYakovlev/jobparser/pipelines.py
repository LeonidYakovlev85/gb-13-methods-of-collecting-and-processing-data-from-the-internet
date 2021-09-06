"""
Принимает оформленную структуры из items.py и производит финальную обработку данных.
Для структуры указываются все методы, классы и функции, формируется конечный документ с нужными нам полями.
Документ либо возвращается, либо помещается в базу данных.
"""
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from pymongo import MongoClient


class JobparserPipeline(object):
    def __init__(self):
        # Подключение к БД
        client = MongoClient('localhost', 27017)
        # Имя БД
        self.mongobase = client['GB_13_05_99_hw_LeonidYakovlev_DB']

    def process_item(self, item, spider):
        """
        :param item: поступивший объект (структура под собранные пауком данные) из items.py
        :param spider: имя паука
        """
        # Создание коллекции с именем паука
        collection = self.mongobase[spider.name]
        # Опредление элементов для помещения в паука
        collection.insert_one(item)
        return item
