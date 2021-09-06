from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from jobparser import settings
from jobparser.spiders.hhru import HhruSpider
from jobparser.spiders.sjru import SjruSpider

if __name__ == '__main__':
    crawler_settings = Settings()  # Инициализация экземпляра настроек
    crawler_settings.setmodule(settings)  # Подключение к нему текущих настроек паука
    process = CrawlerProcess(settings=crawler_settings)  # Инициализация процесса, содержащего созданные настройки
    process.crawl(HhruSpider)  # Вызов метода crawl к пауку
    process.crawl(SjruSpider)  # Вызов метода crawl к пауку
    process.start()  # Запуск процесса
