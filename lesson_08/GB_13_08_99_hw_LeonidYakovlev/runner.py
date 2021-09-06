from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from avitoparser import settings
from avitoparser.spiders.avito import AvitoSpider

if __name__ == '__main__':
    crawler_settings = Settings()  # Инициализация экземпляра настроек
    crawler_settings.setmodule(settings)  # Подключение к нему текущих настроек паука
    process = CrawlerProcess(settings=crawler_settings)  # Инициализация процесса, содержащего созданные настройки
    process.crawl(AvitoSpider, mark='acer')  # Вызов метода crawl к пауку, mark -- ключевое слово для поиска
    process.start()  # Запуск процесса
