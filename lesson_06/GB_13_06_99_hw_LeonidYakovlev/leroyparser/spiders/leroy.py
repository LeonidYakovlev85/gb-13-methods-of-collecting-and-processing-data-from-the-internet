import scrapy
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from ..items import LeroyparserItem


class LeroySpider(scrapy.Spider):
    """
    Класс Spider -- это базовый класс для поисковых роботов, предоставляемый Scrapy.
    Класс Spider предоставляет методы для отслеживания URL-ов и извлечения данных с веб-страниц, но он не знает,
    где искать страницы и какие именно данные нужно извлечь. Чтобы передать классу недостающие данные подкласс.
    Подкласс – это более узкий, специализированный вариант родительского класса.

    Этот класс имеет два обязательных атрибута:
    -- name – название «паука» (или -- имя поискового робота) (под ним будет создана коллекция в MongoDB);
    -- start_urls – список ссылок на страницы, которые нужно проанализировать (или просканировать).
    """
    name = 'leroy'
    allowed_domains = ['leroymerlin.ru']

    # start_urls = ['https://leroymerlin.ru/catalogue/elektroinstrumenty/']

    def __init__(self, keyword):
        # Функция для применения ключевого слова поиска, задаваемого в runner.py
        self.start_urls = [f'https://leroymerlin.ru/catalogue/{keyword}/']

    def parse(self, response):
        # Кнопка «дальше»
        next_page_path = 'a[aria-label*="Следующая страница"]::attr(href)'
        next_page_link = response.css(next_page_path).extract_first()
        next_page_full_link = f'https://leroymerlin.ru{next_page_link}'
        """
        Разделение работы паука на составляющие: один поток будет работать на сбор всех страниц со ссылками 
        на вакансии, второй передаст управление дальше по программе, чтобы собрать информацию с полученной 
        страницы. Метод follow создаёт разветлвление работы программы: одна часть возвращается обратно внутрь 
        метода parse, но в response попадает результат get запроса по next_page.
        """
        yield response.follow(next_page_full_link, callback=self.parse)

        # Ссылки на все объявления, находящиеся на странице
        product_links_path = '//*/div[@class="phytpj4_plp largeCard"]/a/@href'
        product_links = response.xpath(product_links_path).extract()
        for product_link in product_links:
            product_full_link = f'https://leroymerlin.ru{product_link}'
            yield response.follow(product_full_link, callback=self.parse_product)

    def parse_product(self, response):
        # Инициализация объекта класса ItemLoader
        loader = ItemLoader(item=LeroyparserItem(), response=response)
        # id товара
        loader.add_value('_id', response.url)
        # Ссылка на страницу с товаром
        loader.add_value('link', response.url)
        # Наименование товара
        loader.add_css('name', 'h1[slot=title]::text')
        # Параметры товара; Наименование параметра
        loader.add_xpath('parameter_name', "//dt/text()")
        # Параметры товара; Значение параметра
        loader.add_xpath('parameter_value', "//dd/text()")
        # Цена товара
        loader.add_xpath('price', "//meta[@itemprop='price']/@content")
        # Фотографии
        loader.add_xpath('images', '//source[contains(@media, "only screen and (min-width: 768px)")]/@srcset')
        # Передача объекта в items.py для дальнейшей обработки данных
        yield loader.load_item()
