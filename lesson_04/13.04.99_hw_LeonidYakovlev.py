# Импорт библиотек
import os
from pymongo import MongoClient
import requests
import time
from lxml import html
# from lxml import etree
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta


# Создание класса
class NewsParser:

    def __init__(self, headers, domains_list, sleep_time, mongod_path, db_name, collection_name):
        """Инициализация объекта класса"""
        self.headers = headers  # указание заголовков
        self.domains_list = domains_list  # список сайтов
        self.sleep_time = sleep_time  # время задержки между обращениями к сайту
        self.mongod_path = mongod_path  # путь к файлу, запускающему сервер
        self.db_name = db_name  # имя базы данных
        self.collection_name = collection_name  # имя коллекции
        self.db = None  # переменная для подключения к БД
        self.collection = None  # переменная для создания указателя на коллекцию

    def get_root(self, url, params=None):
        """Обращение к странице и преобразование тела документа в дерево элементов (DOM)

        Именованные парметры:
        url -- анализируемая страница
        params -- параметры, необязательный аргумент
        """
        # Определение точного адреса для https://yandex.ru
        url = urljoin(url, 'news') if url == 'https://yandex.ru' else url
        # Обращение к странице до тех пор, пока не будет получен корректный ответ
        # Условие выхода по количеству неудачных итераций не прописано специально, т. к. проект учебный
        while True:
            # Обращение к странице
            response = requests.get(url, headers=self.headers, params=params)
            # Если получен положительный ответ:
            if response.status_code == 200:
                # Преобразование тела документа в дерево элементов (DOM)
                root = html.fromstring(response.text)
                # Возврат результата
                return root
            # Если при получении ответа вернулась ошибка повторное обращение к странице
            time.sleep(self.sleep_time)

    def mail_ru_parse(self, domain, root):
        """Получает информацию о новостях с главной страницы news.mail.ru

        Именованные аргументы:
        domain -- ресурс
        root -- дерево элементов исследуемой страницы
        """
        # Получение всех ссылок на странице
        all_links = root.xpath('//*[@href]/@href')
        # Избавление от возможных дублей
        all_links = list(set(all_links))
        # Фильтрация полученных ссылок по наличию восьмизначного id новости, получение спика новостных ссылок
        news_links = list(filter(lambda link: re.findall('/\d{8}/', link), all_links))
        # Название источника лучше определить на этом этапе, так как он одинаковый для всех новостей
        news_source = re.findall("[a-zA-Z0-9_.]*ru", domain)[0]
        # Обработка новостных ссылок
        for news_link in news_links:
            # Получение информации с новостной страницы в виде дерева элементов
            news_root = self.get_root(news_link)
            # Путь к главному родительскому элементу
            news_parent_unit_path = '//div[@class="cols__inner"]'
            # Путь к элементу с названием новости
            news_title_path = 'h1[@class="hdr__inner"]/text()'
            # Путь к элементу с datetime публикации новости
            news_publication_datetime_path = 'span[@datetime]/@datetime'
            # Создание словаря с данными о новости
            # Название источника -- это news_source
            # Наименование новости
            news_title = news_root.xpath(f'{news_parent_unit_path}//{news_title_path}')[0]
            # Ссылка на новость -- это news_link
            # Дата публикации новости; получение datetime публикации
            news_publication_datetime = news_root.xpath(f'{news_parent_unit_path}//{news_publication_datetime_path}')[0]
            # Дата публикации новости; извлечение даты
            news_publication_date = re.search('\d{4}-\d{2}-\d{2}', news_publication_datetime)[0]
            # Внесение записи в БД
            self.collection.insert_one({
                # _id для MongoDB получается из склейки Unicode для domain и id вакансии
                'Название_источника': news_source,
                'Наименование_новости': news_title,
                'Ссылка_на_новость': news_link,
                'Дата_публикации': news_publication_date,
            })
            # Задержка перед обращением к следующей новости
            time.sleep(self.sleep_time)

    def lenta_ru_parse(self, domain, root):
        """Получает информацию о новостях с главной страницы lenta.ru

        Именованные аргументы:
        domain -- ресурс
        root -- дерево элементов исследуемой страницы
        """
        # Получение всех url на странице
        all_urls = root.xpath('//*[@href]/@href')
        # Избавление от возможных дублей
        all_urls = list(set(all_urls))
        # Фильтрация полученных url -- они должны начинаться с «/news/»
        news_urls = list(filter(lambda url: re.match('/news/', url), all_urls))
        # Название источника лучше определить на этом этапе, так как он одинаковый для всех новостей
        news_source = re.findall("[a-zA-Z0-9_.]*ru", domain)[0]
        # Обработка новостных ссылок
        for news_url in news_urls:
            # Ссылка на новость
            news_link = urljoin(domain, news_url)
            # Получение информации с новостной страницы в виде дерева элементов
            news_root = self.get_root(news_link)
            # Путь к элементу с названием новости; itemprop="headline" встречается на странице только один раз
            news_title_path = '//h1[@itemprop="headline"]/text()'
            # Путь к элементу с datetime публикации новости; time с @pubdate встречается на странице только один раз
            news_publication_datetime_path = '//time[@pubdate]/@datetime'
            # Создание словаря с данными о новости
            # Название источника -- это news_source
            # Наименование новости
            news_title = news_root.xpath(news_title_path)[0]
            # Ссылка на новость -- это news_link
            # Дата публикации новости; получение datetime публикации
            news_publication_datetime = news_root.xpath(news_publication_datetime_path)[0]
            # Дата публикации новости; извлечение даты
            news_publication_date = re.search('\d{4}-\d{2}-\d{2}', news_publication_datetime)[0]
            # Внесение записи в БД
            self.collection.insert_one({
                # _id для MongoDB получается из склейки Unicode для domain и id вакансии
                'Название_источника': news_source,
                'Наименование_новости': news_title,
                'Ссылка_на_новость': news_link,
                'Дата_публикации': news_publication_date,
            })
            # Задержка перед обращением к следующей новости
            time.sleep(self.sleep_time)

    def yandex_ru_parse(self, domain, root):
        """Получает информацию о новостях с главной страницы news.mail.ru

        Именованные аргументы:
        domain -- ресурс
        root -- дерево элементов исследуемой страницы
        """
        # Получение всех родительских элементов с новостными ссылками
        news_article_tags = root.xpath('//*/article')
        # Обработка родительских элементов
        for news_article_tag in news_article_tags:
            # Название источника; Определение первоисточника
            news_origin_source = news_article_tag.xpath('.//a[last()]/text()')[0]
            # Название источника; Формирование итоговой записи
            news_source = f'yandex.ru / {news_origin_source}'
            # Наименование новости
            news_title = news_article_tag.xpath('.//h2/text()')[0]
            # Ссылка на новость; Внутрення ссылка yandex.ru
            news_internal_yandex_link = news_article_tag.xpath('.//a[last()]/@href')[0]
            news_link = news_internal_yandex_link
            # Ссылка на новость; Получение ссылки на первоисточник
            # Переход по внутренней ссылке; Получение дерева элементов; Извлечение ссылки на первоисточник
            # (выполнить не удаётся в связи с блокировкой из-за превышения количества обращений)
            # news_root = self.get_root(news_internal_yandex_link)
            # news_link = news_root.xpath('//*/a[@class="news-story__title-link"]/@href')[0]
            # Дата публикации; Получение времени публикации
            news_publication_time = news_article_tag.xpath('.//span[@class="mg-card-source__time"]/text()')[0]
            # Дата публикации; Проверка наличия маркера «вчера» и присвоение даты
            if 'вчера' in news_publication_time:
                news_publication_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%d-%m')
            else:
                news_publication_date = datetime.now().strftime('%Y-%d-%m')
            # Внесение записи в БД
            self.collection.insert_one({
                # _id для MongoDB получается из склейки Unicode для domain и id вакансии
                'Название_источника': news_source,
                'Наименование_новости': news_title,
                'Ссылка_на_новость': news_link,
                'Дата_публикации': news_publication_date,
            })

    def root_parse(self, domain, root):
        """Парсинг дерева элементов страницы

        Именованные параметры:
        domain -- ресурс
        root -- дерево элементов исследуемой страницы
        """
        # Если анализируется news.mail.ru
        if domain == 'https://news.mail.ru':
            self.mail_ru_parse(domain, root)
        # Если анализируется lenta.ru
        elif domain == 'https://lenta.ru':
            self.lenta_ru_parse(domain, root)
        # Если анализируется yandex.ru
        elif domain == 'https://yandex.ru':
            self.yandex_ru_parse(domain, root)

    def run(self):
        """Запуск парсера для создания и наполнения базы"""
        # Запуск сервера Mongo DB
        os.startfile('C:/Program Files/MongoDB/Server/4.2/bin/mongod.exe')
        # Создание клиента для подключения к серверу
        client = MongoClient('localhost', 27017)
        # Подключение к БД
        self.db = client[self.db_name]
        # Создание указателя на коллекцию, чтобы было проще проще обращаться к ней
        self.collection = self.db[self.collection_name]
        # Перебор списка сайтов
        for domain in self.domains_list:
            # Получение дерева элементов главной страницы
            root = self.get_root(domain)
            # Анализ и получение информации
            self.root_parse(domain, root)


# Указание заголовков
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/90.0.4430.212 Safari/537.36 OPR/76.0.4017.154'}
# Указание ресурсов для сбора новостей
domains_list = ['https://news.mail.ru', 'https://lenta.ru', 'https://yandex.ru']
# Время задержки между обращениями к сайту
sleep_time = 0.25
# Путь к файлу, запускающему сервер
mongod_path = 'C:/Program Files/MongoDB/Server/4.2/bin/mongod.exe'
# Имя базы данных
db_name = 'news_database'
# Имя коллекции
collection_name = 'news_collection'
# Инициализация объекта парсера
parser = NewsParser(headers, domains_list, sleep_time, mongod_path, db_name, collection_name)
# Запуск парсера
parser.run()
