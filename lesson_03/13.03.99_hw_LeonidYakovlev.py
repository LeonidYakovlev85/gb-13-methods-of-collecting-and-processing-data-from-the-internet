# Импорт библиотек
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
import os
import requests
import re
from urllib.parse import urljoin
import time
from datetime import datetime


class HhSjParser:

    def __init__(self, headers, pages_count, mongod_path, db_name, collection_name):
        """Инициализация объекта класса"""
        self.domains_list = ['hh.ru', 'superjob.ru']  # список сайтов
        self.headers = headers  # указание заголовков
        self.pages_count = pages_count  # число страниц для обхода
        self.mongod_path = mongod_path  # путь к файлу, запускающему сервер
        self.db_name = db_name  # имя базы данных
        self.collection_name = collection_name  # имя коллекции
        self.db = None  # переменная для подключения к БД
        self.collection = None  # переменная для создания указателя на коллекцию
        self.sleep_time = 0.5  # время задержки между обращениями к сайту

    def start_url(self, domain):
        """Определение стартовой страницы

        Именованные парметры:
        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        """
        if domain == 'hh.ru':
            url = f'https://spb.{domain}/vacancies/analitik-big-data'
        else:
            url = f'https://spb.{domain}/vacancy/search/?keywords=аналитик%20Big%20Data'
        return url

    def get_soup(self, url):
        """Получение страницы в виде объекта BeautifulSoup

        Именованные парметры:
        url -- адрес страницы
        """
        # Обращение к странице
        response = requests.get(url, headers=self.headers).text
        # Получение объекта BeautifulSoup
        soup = bs(response, 'html.parser')
        return soup

    def get_parent_divs(self, domain, soup):
        """Получение массива родительских элементов каждой вакансии на странице

        Именованные парметры:
        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        soup -- исследуемая страница в виде объекта BeautifulSoup
        """
        if domain == 'hh.ru':
            parent_divs = soup.find_all(name='div', attrs={'class': 'vacancy-serp-item'})
        else:
            parent_divs = soup.find_all(name='div', attrs={'class': 'Fo44F QiY08 LvoDO'})
        return parent_divs

    def get_salary(self, domain, parent_div):
        """Определение минимальной и максимальной зарплат, а также валюты

        Именованные парметры:
        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        parent_div -- родительский элемент вакансии, содержащий в том числе и информацию о зарплате
        """
        # Поиск элемента с данными о зарплате
        if domain == 'hh.ru':
            salary_element = parent_div.find(
                name='span',
                attrs={'data-qa': 'vacancy-serp__vacancy-compensation'}
            )
        else:
            salary_element = parent_div.find(
                name='span',
                attrs={'class': '_1h3Zg _2Wp8I _2rfUm _2hCDz _2ZsgW'}
            )
        # Если элемент с данными о зарплате есть
        if salary_element:
            # Получение содержимого зарплатного элемента, преобразование в str и удаление пробелов внутри чисел
            if domain == 'hh.ru':
                salary = ''.join(salary_element.text.split(' '))  # здесь внутри числа неразрывный пробел
            else:
                salary = ''.join(salary_element.text.split('\xa0'))
            # Если зарплата 'по договорённости'
            if salary == 'По договорённости':
                min_salary = max_salary = 'По договорённости'
                currency = '---'
            # Если указана вилка зарплаты
            elif ('–' in salary) or ('—' in salary):  # (hh и sj используют разные типы дефисов)
                min_salary = int(re.findall('\d+', salary)[0])
                max_salary = int(re.findall('\d+', salary)[1])
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
            # Если указан только нижний порог зарплаты
            elif 'от' in salary:
                min_salary = int(re.findall('\d+', salary)[0])
                max_salary = '---'
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
            # Если указан только верхний порог зарплаты
            elif 'до' in salary:
                min_salary = '---'
                max_salary = int(re.findall('\d+', salary)[0])
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
            # Если указана конкретная сумма
            else:
                min_salary = max_salary = re.findall('\d+', salary)[0]
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
        # Если элемент с данными о зарплате отсутствует
        else:
            min_salary = max_salary = 'Зарплата не указана'
            currency = '---'
        return min_salary, max_salary, currency

    def hh_vacancy_to_mongodb(self, domain, url, parent_div):
        """Проверяет наличие вакансии в БД и, в случае отсутствия, получает информацию о ней

        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        url -- адрес страницы
        parent_div -- родительский элемент вакансии
        """
        # Получаем "грязную ссылку"
        dirty_link = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).attrs['href']
        # Разделяем "грязную ссылку" по "/", обращаемся к части с id и удаляем "мусор", после символа "?"
        # получаем id
        vacancy_id = int(dirty_link.split('/')[4].split('?')[0])
        # Проверка наличия вакансии в БД
        mongo_id = f'hhru{vacancy_id}'
        if mongo_id not in set(map(lambda x: x['_id'], self.collection.find())):
            # Наименование вакансии hh
            vacancy_name = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).text
            # Зарплата hh
            min_salary, max_salary, currency = self.get_salary(domain, parent_div)
            # Ссылка на вакансию
            vacancy_link = urljoin('https://spb.hh.ru/vacancy/', str(vacancy_id))
            # Работодатель hh
            employer = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).text
            employer = employer.replace('\xa0', ' ')  # Избавление от 'мусора' только для hh
            # Запись вакансии в БД
            self.collection.insert_one({
                # _id для MongoDB получается из склейки Unicode для domain и id вакансии
                '_id': mongo_id,
                'id_вакансии': vacancy_id,
                'Наименование_вакансии': vacancy_name,
                'Минимальная_зарплата': min_salary,
                'Максимальная_зарплата': max_salary,
                'Валюта': currency,
                'Ссылка': vacancy_link,
                'Работодатель': employer,
                'Рекрутинговый_сайт': domain,
                'Время_добавления_в_БД': datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    def sj_vacancy_to_mongodb(self, domain, url, parent_div):
        """Проверяет наличие вакансии в БД и, в случае отсутствия, получает информацию о ней

        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        url -- адрес страницы
        parent_div -- родительский элемент вакансии
        """
        # Получаем "грязную ссылку"
        dirty_link = parent_div.find(name='a', attrs={'target': '_blank'}).attrs['href']
        # Разделяем "грязную ссылку" по "-", обращаемся к части с id и удаляем ".html"
        # получаем id
        vacancy_id = int(dirty_link.split('-')[-1].replace('.html', ''))
        # Проверка наличия вакансии в БД
        mongo_id = f'sjru{vacancy_id}'
        if mongo_id not in set(map(lambda x: x['_id'], self.collection.find())):
            # Наименование вакансии sj
            vacancy_name = parent_div.find(name='a', attrs={'target': '_blank'}).text
            # Зарплата sj
            min_salary, max_salary, currency = self.get_salary(domain, parent_div)
            # Ссылка на вакансию sj
            vacancy_link = urljoin(url, dirty_link)
            # Работодатель sj
            employer = parent_div.find(name='a', attrs={'target': '_self'}).text
            # Запись вакансии в БД
            self.collection.insert_one({
                # _id для MongoDB получается из склейки Unicode для domain и id вакансии
                '_id': mongo_id,
                'id_вакансии': vacancy_id,
                'Наименование_вакансии': vacancy_name,
                'Минимальная_зарплата': min_salary,
                'Максимальная_зарплата': max_salary,
                'Валюта': currency,
                'Ссылка': vacancy_link,
                'Работодатель': employer,
                'Рекрутинговый_сайт': domain,
                'Время_добавления_в_БД': datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    def soup_parse(self, domain, url, soup):
        """Обработка страницы в виде объекта BeautifulSoup

        Именованные парметры:
        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        url -- адрес исследуемой страницы
        soup -- исследуемая страница в виде объекта BeautifulSoup
        """
        # Получение массива родительских элементов каждой вакансии на странице
        parent_divs = self.get_parent_divs(domain, soup)
        # Перебор всех блоков с вакансиями
        for parent_div in parent_divs:
            if domain == 'hh.ru':
                self.hh_vacancy_to_mongodb(domain, url, parent_div)
            else:
                self.sj_vacancy_to_mongodb(domain, url, parent_div)

    def get_next_page_link(self, domain, soup):
        """Получение ссылки на следующую страницу

        Именованные парметры:
        domain -- маркер сайта ('hh.ru' или 'superjob.ru')
        soup -- исследуемая страница в виде объекта BeautifulSoup
        """
        # Обращение к а-тегу кнопки 'дальше'
        if domain == 'hh.ru':
            next_page_link = soup.find(
                name='a',
                attrs={'class': 'bloko-button', 'data-qa': 'pager-next'}
            )
        else:
            next_page_link = soup.find(
                name='a',
                attrs={'rel': 'next'}
            )
        return next_page_link

    def run(self):
        """Запуск парсера для создания и наполнения базы"""
        # Запуск сервера Mongo DB
        os.startfile(self.mongod_path)
        # Создание клиента для подключения к серверу
        client = MongoClient('localhost', 27017)
        # Подключение к БД
        self.db = client[self.db_name]
        # Создание указателя на коллекцию, чтобы было проще проще обращаться к ней
        self.collection = self.db[self.collection_name]
        # Перебор списка сайтов
        for domain in self.domains_list:
            # Определение стартового url
            start_url = self.start_url(domain)
            url = start_url
            # Парсинг сайта в соответствии с заданным числом страниц для прохода
            for i in range(self.pages_count):
                # Получение страницы в виде объекта BeautifulSoup
                soup = self.get_soup(url)
                # Обработка полученной страницы, внесение данных о вакансиях в self.vacancies_list
                self.soup_parse(domain, url, soup)
                # Получение ссылки на следующую страницу
                next_page_link = self.get_next_page_link(domain, soup)
                # Если переход на следующую страницу существует, то обновление url
                if next_page_link:
                    url = urljoin(url, next_page_link.attrs['href'])
                # Если перехода на следующую страницу нет, то выход из цикла
                else:
                    break
                # Задержка перед обращением к следующей странице
                time.sleep(self.sleep_time)


def delicious_vacancies(mongod_path, db_name, collection_name, lower_wage):
    """производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы

    mongod_path -- путь к файлу, запускающему сервер
    db_name -- имя базы данных
    collection_name -- имя коллекции
    lower_wage -- нижний уровень зарплаты (применительно к любому из порогов)
    """
    # Запуск сервера Mongo DB
    os.startfile(mongod_path)
    # Создание клиента для подключения к серверу
    client = MongoClient('localhost', 27017)
    # Подключение к БД
    db = client[db_name]
    # Создание указателя на коллекцию, чтобы было проще проще обращаться к ней
    collection = db[collection_name]
    for vacansy in collection.find({'$or': [
        {'$and': [
            {'Минимальная_зарплата': {'$type': 'int'}},  # проверка наличия нижнего порога
            {'Минимальная_зарплата': {'$gte': lower_wage}}  # проверка соответствия нижнего порога условию
        ]},
        {'$and': [
            {'Максимальная_зарплата': {'$type': 'int'}},  # проверка наличия верхнего порога
            {'Максимальная_зарплата': {'$gte': lower_wage}}  # проверка соответствия верхнего порога условию
        ]}
    ]}):
        for key, value in vacansy.items():
            print(f'{key}: {value}')
        print('_' * 50)


# Указание заголовков
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/90.0.4430.212 Safari/537.36 OPR/76.0.4017.154'}
# Указание количества страниц для обхода
pages_count = 5
# Путь к файлу, запускающему сервер
mongod_path = 'C:/Program Files/MongoDB/Server/4.2/bin/mongod.exe'
# Имя базы данных
db_name = 'vacancies_database'
# Имя коллекции
collection_name = 'vacancies_collection'
# Инициализация объекта парсера
parser = HhSjParser(headers, pages_count, mongod_path, db_name, collection_name)
# Запуск парсера
parser.run()

# Вывод вакансий по минимальному значению
delicious_vacancies(mongod_path, db_name, collection_name, 100000)
