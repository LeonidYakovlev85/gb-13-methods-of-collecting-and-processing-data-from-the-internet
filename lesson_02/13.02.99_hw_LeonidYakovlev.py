from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
from urllib.parse import urljoin
import time


class HhSjParser:

    def __init__(self, headers_arg, pages_count_arg):
        """Инициализация объекта класса"""
        self.domains_list = ['hh.ru', 'superjob.ru']  # Список сайтов
        self.pages_count = pages_count_arg  # Число страниц для обхода
        self.headers = headers_arg  # Указание заголовков
        self.vacancies_list = []  # # Инициализация общего списка вакансий
        self.sleep_time = 0.5  # Время задержки между обращениями к сайту

    def start_url(self, domain_arg):
        """Определение стартовой страницы"""
        if domain_arg == 'hh.ru':
            url = f'https://spb.{domain_arg}/vacancies/analitik-big-data'
        else:
            url = f'https://spb.{domain_arg}/vacancy/search/?keywords=аналитик%20Big%20Data'
        return url

    def get_soup(self, url_arg):
        """Получение страницы в виде объекта BeautifulSoup"""
        # Обращение к странице
        response = requests.get(url_arg, headers=headers).text
        # Получение объекта BeautifulSoup
        soup = bs(response, 'html.parser')
        return soup

    def get_salary(self, domain_arg, parent_div_arg):
        """Определение минимальной и максимальной зарплат, а также валюты"""
        # Поиск элемента с данными о зарплате
        if domain_arg == 'hh.ru':
            salary_element = parent_div_arg.find(
                name='span',
                attrs={'data-qa': 'vacancy-serp__vacancy-compensation'}
            )
        else:
            salary_element = parent_div_arg.find(
                name='span',
                attrs={'class': '_1h3Zg _2Wp8I _2rfUm _2hCDz _2ZsgW'}
            )
        # Если элемент с данными о зарплате есть
        if salary_element:
            # Получение содержимого зарплатного элемента для hh и для sj
            if domain_arg == 'hh.ru':
                # Преобразование в str и удаление пробелов внутри чисел
                salary = ''.join(salary_element.text.split(' '))
            else:
                # Преобразование в str и удаление пробелов внутри чисел
                salary = ''.join(salary_element.text.split('\xa0'))
            # Если зарплата "по договорённости"
            if salary == 'По договорённости':
                min_salary = max_salary = 'По договорённости'
                currency = '---'
            # Если указана вилка зарплаты
            elif '—' in salary:
                min_salary = re.findall('\d+', salary)[0]
                max_salary = re.findall('\d+', salary)[1]
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
            # Если указан только нижний порог зарплаты
            elif 'от' in salary:
                min_salary = re.findall('\d+', salary)[0]
                max_salary = '---'
                currency = re.findall('[А-Яа-яA-Za-z.]+', salary)[-1]
            # Если указан только верхний порог зарплаты
            elif 'до' in salary:
                min_salary = '---'
                max_salary = re.findall('\d+', salary)[0]
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

    def soup_parse(self, domain_arg, url_arg, soup_arg):
        """Обработка страницы в виде объекта BeautifulSoup"""
        # Получение списка родительских элементов каждой вакансии на странице
        if domain_arg == 'hh.ru':
            parent_divs = soup_arg.find_all(name='div', attrs={'class': 'vacancy-serp-item'})
        else:
            parent_divs = soup_arg.find_all(name='div', attrs={'class': 'Fo44F QiY08 LvoDO'})
        # Перебор всех блоков с вакансиями
        for parent_div in parent_divs:
            if domain_arg == 'hh.ru':
                # Наименование вакансии
                vacancy_name = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).text
                # Зарплата
                min_salary, max_salary, currency = self.get_salary(domain_arg, parent_div)
                # Ссылка на вакансию
                link = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).attrs['href']
                # Работодатель
                employer = parent_div.find(name='a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).text
                # Избавление от "мусора"
                employer = employer.replace('\xa0', ' ')  # только для hh
            else:
                # Наименование вакансии
                vacancy_name = parent_div.find(name='a', attrs={'target': "_blank"}).text
                # Зарплата
                min_salary, max_salary, currency = self.get_salary(domain_arg, parent_div)
                # Ссылка на вакансию
                link = urljoin(url_arg, parent_div.find(name='a', attrs={'target': "_blank"}).attrs['href'])
                # Работодатель
                employer = parent_div.find(name='a', attrs={'target': '_self'}).text
            # Создание словаря с данными о вакансии
            vacancy_dict = {
                'Наименование_вакансии': vacancy_name,
                'Минимальная_зарплата': min_salary,
                'Максимальная_зарплата': max_salary,
                'Валюта': currency,
                'Ссылка': link,
                'Работодатель': employer,
                'Рекрутинговый_сайт': domain_arg
            }
            # Внесение данных о вакансии в общий список
            self.vacancies_list.append(vacancy_dict)

    def run(self):
        """Запуск парсера"""
        # Перебор списка сайтов
        for domain in self.domains_list:
            # Определение стартового url
            url = self.start_url(domain)
            # Парсинг сайта в соответствии с заданным числом страниц для прохода
            for i in range(self.pages_count):
                # Получение страницы в виде объекта BeautifulSoup
                soup = self.get_soup(url)
                # Обработка полученной страницы, внесение данных о вакансиях в self.vacancies_list
                self.soup_parse(domain, url, soup)
                time.sleep(self.sleep_time)
                # Обращение к а-тегу кнопки "дальше"
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
                # Если переход на следующую страницу существует, то обновление url
                if next_page_link:
                    url = urljoin(url, next_page_link.attrs['href'])
                # Если перехода на следующую страницу нет, то выход из цикла
                else:
                    break
        # Создание датафрейма с данными о вакансиях
        vacancies_df = pd.DataFrame(data=self.vacancies_list)
        # Экспорт датафрейма в MS Excel
        vacancies_df.to_excel('13.02.99_hw_data_file.xlsx')


# Указание заголовков
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/90.0.4430.212 Safari/537.36 OPR/76.0.4017.154'}
# Указание количества страниц для обхода
pages_count = 5
# Инициализация объекта парсера
parser = HhSjParser(headers, pages_count)
# Запуск парсера
parser.run()
