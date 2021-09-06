import scrapy
# Чтобы были доступны различные методы для response
from scrapy.http import HtmlResponse
# Для передачи в дальнейшем информации в items.py
# from GB_13_05_02_02_avitoparser.avitoparser.items import AvitoparserItem
from ..items import AvitoparserItem
from scrapy.loader import ItemLoader


class AvitoSpider(scrapy.Spider):
    """
    Класс Spider -- это базовый класс для поисковых роботов, предоставленный Scrapy.
    Класс Spider предоставляет методы для отслеживания URL-ов и извлечения данных с веб-страниц, но он не знает,
    где искать страницы и какие именно данные нужно извлечь. Чтобы передать классу недостающие данные подкласс.
    Подкласс – это более узкий, специализированный вариант родительского класса.

    Этот класс имеет два обязательных атрибута:
    -- name – название «паука» (или -- имя поискового робота) (под ним будет создана коллекция в MongoDB);
    -- start_urls – список ссылок на страницы, которые нужно проанализировать (или просканировать).
    """
    name = 'avito'
    allowed_domains = ['avito.ru']

    def __init__(self, mark):
        # mark -- ключевое слово для поиска
        self.start_urls = [f'https://www.avito.ru/rossiya/bytovaya_elektronika?q={mark}']

    def parse(self, response: HtmlResponse):
        # Ссылки на все объявления, находящиеся на странице
        links_path = '//*/a[@data-marker="item-title"]/@href'
        ads_links = response.xpath(links_path).extract()
        """
        Разделение работы паука на составляющие: один поток будет работать на сбор всех страниц со ссылками 
        на вакансии, второй передаст управление дальше по программе, чтобы собрать информацию с полученной 
        страницы. Метод follow создаёт разветлвление работы программы: одна часть возвращается обратно внутрь 
        метода parse, но в response попадает результат get запроса по next_page
        """
        for link in ads_links:
            full_link = f'https://www.avito.ru/{link}'
            yield response.follow(full_link, callback=self.parse_ads)

    def parse_ads(self, response: HtmlResponse):
        # Наименование товара
        name_path = 'span.title-info-title-text::text'
        name = response.css(name_path).extract_first()
        # Стоимость товара
        price_path = '//*/span[@class="js-item-price"]/text()'
        price = response.xpath(price_path).extract()[1]
        # Фотографии товара
        photos_path = '//div[contains(@class, "gallery-img-wrapper")]' \
                      '//div[contains(@class, "gallery-img-frame")]/@data-url'
        photos = response.xpath(photos_path).extract()
        # Инициализация объекта AvitoparserItem для дальнейшей обработки данных
        yield AvitoparserItem(name=name, photos=photos, price=price)
