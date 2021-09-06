"""
Принимает оформленную структуры из items.py и производит финальную обработку данных.
Для структуры указываются все методы, классы и функции, формируется конечный документ с нужными полями.
Документ либо возвращается, либо помещается в базу данных.
"""
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import scrapy
from scrapy.pipelines.images import ImagesPipeline
import re
import os
from pymongo import MongoClient


class LeroyDataBasePipeline:
    def __init__(self):
        # Подключение к БД
        client = MongoClient('localhost', 27017)
        # Имя БД
        self.mongo_base = client['GB_13_06_99_hw_LeonidYakovlev_DB']

    def process_item(self, item, spider):
        """
        Заключительная обработка данных о товаре, создание БД и наполнение её обработанными данными.
        :param item: объект поступивший из items.py (структура под собранные пауком данные).
        :param spider: паук.
        """
        # Наполнение parameters данными из parameter_name и parameter_value
        item['parameters'] = {
            item['parameter_name'][i]: item['parameter_value'][i] for i in range(len(item['parameter_name']))
        }
        # Удаление данных, ставших ненужными
        del item['parameter_name'], item['parameter_value']

        # Создание коллекции с именем паука
        collection = self.mongo_base[spider.name]
        # Опредление элементов для помещения в паука
        collection.update_one({'link': item['link']}, {'$set': item}, upsert=True)
        # print('collection_updated')
        return item


# Класс для фотографий, сюда они попадают перед DataBasePipeline
class LeroyImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        """
        Извлечение ссылок на страницы с изображениями из item['images'] и их поочерёдная
        передача в file_path для дальнейшей обработки
        """
        if item['images']:
            for image_page_link in item['images']:
                yield scrapy.Request(image_page_link)
        else:
            print(f'{item["_id"]} has no images')

    def file_path(self, request, response=None, info=None):
        """
        Производится пределение пути для файла с изображением.
        Общий вид: путь_к_директории_с_изображениями_товара / имя_файла.

        Путь к директории с изображениями товара.
        Общий вид: путь к текущей директории / директория «images» / директория «product_id».
        Фрагмент «product_id» извлекается из request.url;
        «images» -- значение параметра IMAGES_STORE из settings.py;
        путь к текущей директории определяется с помощью os.getcwd().

        Имя файла.
        Из request.url с помощью os.path.basename берётся базовое имя файла или «хвост»,
        состоящее из имени файла и расширения.

        Передача полученного пути к файлу в item_completed для заключительной обработки.

        :param request: запрос по ссылке на страницу с изображением из get_media_requests.
        """
        # request.url имеет вид «https://res.cloudinary.com/.../18680876_01.jpg»
        # Из ссылки выбирается участок, начинающийся на «/» и любую цифру
        pattern = re.compile('\/(\d+)')
        product_id = re.findall(pattern, request.url)[0]
        dir_path = f'{os.getcwd()}\\images\\{product_id}\\'
        # Если директория не существует, то она создаётся
        if os.path.exists(dir_path) == False:
            os.mkdir(dir_path)
        # Имя файла
        file_name = os.path.basename(request.url)
        # Полный путь к файлу
        file_path = f'{dir_path}{file_name}'
        return file_path

    def item_completed(self, results, item, info):
        """
        Заключительная обработка данных с изображениями. Если файл с изображением существует, то его данные
        передаются в item['images']

        :param results: список кортежей для каждого изображения, включающих в себя:
            - проверку на наличие изображения (True или False);
            - словарь с данными изображения (url, path, checksum status).
        :param item: объект класса LeroyparserItem
        """
        if results[0]:
            item['images'] = [image_tuple[1] for image_tuple in results if image_tuple[0]]
        return item
