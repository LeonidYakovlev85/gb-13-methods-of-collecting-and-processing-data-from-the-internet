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
import scrapy
from pymongo import MongoClient
# Для работы с фотографиями
from scrapy.pipelines.images import ImagesPipeline
import csv


# Исходный класс
# class AvitoparserPipeline:
#     def process_item(self, item, spider):
#         return item

# Самостоятельно созданный класс
class DataBasePipeline(object):
    def __init__(self):
        # Подключение к БД
        client = MongoClient('localhost', 27017)
        # Имя БД
        self.mongo_base = client['GB_13_08_99_hw_LeonidYakovlev_DB']

        # Инициализация файла для сохранения данных, он должен быть предварительно создан
        # self.file = f'D:/avito_database.csv'
        self.file = f'GB_13_08_99_hw_LeonidYakovlev_DB.csv'
        # Открытие файла на чтение
        with open(self.file, 'r', newline='') as csv_file:
            # Чтение файла и заполнение self.tmp_data результатом, полученным из свойства fieldnames
            self.tmp_data = csv.DictReader(csv_file).fieldnames
        # Открытие файла на чтение без оператора with, т. к. файл должен быть открыт всё время существования класса
        self.csv_file = open(self.file, 'a', newline='', encoding='UTF-8')

    def process_item(self, item, spider):
        """
        :param item: поступивший объект (структура под собранные пауком данные) из items.py
        :param spider: имя паука
        """
        # Создание коллекции с именем паука
        collection = self.mongo_base[spider.name]
        # Опредление элементов для помещения в паука
        collection.insert_one(item)

        # Считывание значений всех ключей пришедшего item, чтобы определить заголовки столбцов для файла CSV
        columns = item.fields.keys()
        # Создание объекта DictWriter, чтобы иметь возможность записывать данные в файл
        data = csv.DictWriter(self.csv_file, columns)
        # Если self.tmp_data пустой, то нужно создать строку с наименованием столбцов
        if not self.tmp_data:
            data.writeheader()
            self.tmp_data = True
        # Запись данных, пришедших из item в файл
        data.writerow(item)

        return item

    def __del__(self):
        # Закрытие файла после прекращения существования класса
        self.csv_file.close()


# Класс для фотографий, сюда они попадают перед DataBasePipeline
class AvitoPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for img in item['photos']:
                try:
                    yield scrapy.Request(img)
                # Если фотографий нет, печатать «e»
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results if itm[0]]
        return item
