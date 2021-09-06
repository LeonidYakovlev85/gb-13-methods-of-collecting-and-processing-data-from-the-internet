import scrapy
# Чтобы были доступны различные методы для response
from scrapy.http import HtmlResponse
# Для передачи в дальнейшем информации в items.py
from GB_13_05_99_hw_LeonidYakovlev.jobparser.items import JobparserItem
# from scrapy.loader import ItemLoader


class SjruSpider(scrapy.Spider):
    """
    Базовый класс для поисковых роботов.
    Класс Spider предоставляет методы для отслеживания URL и извлечения данных с веб-страниц. Он не знает, где
    искать страницы и какие именно данные нужно извлечь, для передачи классу недостающих данных создаётся подкласс
    """
    # Имя паука, под ним будет создана коллекция в MongoDB
    name = 'sjru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://spb.superjob.ru/vacancy/search/?keywords=python']

    def parse(self, response: HtmlResponse, **kwargs):
        # Кнопка «дальше»
        next_page = response.css('a[rel=next]::attr(href)').extract()[1]
        """
        Разделение работы паука на составляющие: один поток будет работать на сбор всех страниц со ссылками
        на вакансии, второй передаст управление дальше по программе, чтобы собрать информацию с полученной
        страницы. Метод follow создаёт разветлвление работы программы: одна часть возвращается обратно внутрь
        метода parse, но в response попадает результат get запроса по next_page
        """
        yield response.follow(next_page, callback=self.parse)
        # Получение всех ссылок на вакансии
        vacancy = response.css(
            'div.f-test-search-result-item div[spacing="3"] a[target=_blank]::attr(href)'
        ).extract()
        # Обработка каждой ссылки на вакансию
        for link in vacancy:
            yield response.follow(f'https://spb.superjob.ru{link}', callback=self.vacansy_parse)

    def vacansy_parse(self, response: HtmlResponse):
        # Наименование вакансии
        vacancy_name = response.css('div.f-test-vacancy-base-info h1::text').extract_first()
        # Заработная плата
        salary = response.css(
            'div.f-test-vacancy-base-info span[class="_1h3Zg _2Wp8I _2rfUm _2hCDz"]::text').extract()

        # Определение минимальной и максимальной заработной платы, а также валюты
        # Если заработная плата «По договорённости»
        if 'По договорённости' in salary:
            min_salary = max_salary = 'По договорённости'
            currency = '---'
        # Если указан только нижний порог зарплаты
        # Избавление от   => выборка числовых составляющих => их объединение
        elif 'от' in salary:
            min_salary = ' '.join(salary[2].split(' ')[:-1])
            max_salary = '---'
            currency = salary[2].split(' ')[-1]
        # Если указан только верхний порог зарплаты
        # Избавление от   => выборка числовых составляющих => их объединение
        elif 'до' in salary:
            min_salary = '---'
            max_salary = ' '.join(salary[2].split(' ')[:-1])
            currency = salary[2].split(' ')[-1]
        # Если указана вилка зарплаты
        else:
            min_salary = salary[0].replace(' ', ' ')
            max_salary = salary[1].replace(' ', ' ')
            currency = salary[-1]
        # Ссылка на вакансию, избавление от лишней составляющей адреса
        vacancy_link = response.url.replace('?from=vacancy_search_list&query=python', '')
        # Сайт, откуда собрана вакансия
        domain = 'SuperJob.ru'

        # Инициализация объекта JobparserItem для дальнейшей обработки данных
        yield JobparserItem(vacancy_name=vacancy_name,
                            min_salary=min_salary,
                            max_salary=max_salary,
                            currency=currency,
                            vacancy_link=vacancy_link,
                            domain=domain)
