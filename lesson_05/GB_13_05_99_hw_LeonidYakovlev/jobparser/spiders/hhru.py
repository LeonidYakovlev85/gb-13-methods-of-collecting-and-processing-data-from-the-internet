import scrapy
# Чтобы были доступны различные методы для response
from scrapy.http import HtmlResponse
# Для передачи в дальнейшем информации в items.py
from GB_13_05_99_hw_LeonidYakovlev.jobparser.items import JobparserItem
# from scrapy.loader import ItemLoader


class HhruSpider(scrapy.Spider):
    """
    Базовый класс для поисковых роботов.
    Класс Spider предоставляет методы для отслеживания URL и извлечения данных с веб-страниц. Он не знает, где
    искать страницы и какие именно данные нужно извлечь, для передачи классу недостающих данных создаётся подкласс
    """
    # Имя паука, под ним будет создана коллекция в MongoDB
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://spb.hh.ru/search/vacancy?area=&st=searchVacancy&text=python']

    def parse(self, response: HtmlResponse, **kwargs):
        # Кнопка «дальше»
        next_page = response.css('a[data-qa*=pager-next]::attr(href)').extract_first()
        """
        Разделение работы паука на составляющие: один поток будет работать на сбор всех страниц со ссылками 
        на вакансии, второй передаст управление дальше по программе, чтобы собрать информацию с полученной 
        страницы. Метод follow создаёт разветлвление работы программы: одна часть возвращается обратно внутрь 
        метода parse, но в response попадает результат get запроса по next_page
        """
        yield response.follow(next_page, callback=self.parse)
        # Получение всех ссылок на вакансии
        vacancy = response.css(
            'div.vacancy-serp div.vacancy-serp-item div.vacancy-serp-item__row_header a.bloko-link::attr(href)'
        ).extract()
        # Обработка каждой ссылки на вакансию
        for link in vacancy:
            yield response.follow(link, callback=self.vacansy_parse)

    def vacansy_parse(self, response: HtmlResponse):
        # Наименование вакансии
        vacancy_name = response.css('div.vacancy-title h1.bloko-header-1::text').extract_first()
        # Заработная плата
        salary = response.css(
            'div.vacancy-title p.vacancy-salary span[data-qa=bloko-header-2]::text').extract()[0]

        # Определение минимальной и максимальной заработной платы, а также валюты
        # Если заработная плата «не указана»
        if salary == 'з/п не указана':
            min_salary = max_salary = 'Заработная плата не указана'
            currency = '---'
        # Если заработная плата указана
        else:
            # Разбиение строки на составные части по пробелу, внутри чисел неразрыный пробел -- « »
            salary = salary.split(' ')
            # Если указана вилка зарплаты
            if 'от' in salary and 'до' in salary:
                min_salary = salary[1].replace(' ', ' ')
                max_salary = salary[3].replace(' ', ' ')
            # Если указан только нижний порог зарплаты
            elif 'от' in salary:
                min_salary = salary[1].replace(' ', ' ')
                max_salary = '---'
            # Если указан только верхний порог зарплаты
            elif 'до' in salary:
                min_salary = '---'
                max_salary = salary[1].replace(' ', ' ')
            # Если указана конкретная сумма
            else:
                min_salary = max_salary = salary[0].replace(' ', ' ')
            currency = salary[-1]
        # Ссылка на вакансию, избавление от лишней составляющей адреса
        vacancy_link = response.url.replace('?from=vacancy_search_list&query=python', '')
        # Сайт, откуда собрана вакансия
        domain = 'HH.ru'

        # Инициализация объекта JobparserItem для дальнейшей обработки данных
        yield JobparserItem(vacancy_name=vacancy_name,
                            min_salary=min_salary,
                            max_salary=max_salary,
                            currency=currency,
                            vacancy_link=vacancy_link,
                            domain=domain)
