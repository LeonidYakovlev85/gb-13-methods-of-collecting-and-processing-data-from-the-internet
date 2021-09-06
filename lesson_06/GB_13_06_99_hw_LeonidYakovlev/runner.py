from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from leroyparser import settings
from leroyparser.spiders.leroy import LeroySpider

if __name__ == '__main__':
    # Инициализация экземпляра настроек
    crawler_settings = Settings()
    # Подключение к нему текущих настроек паука
    crawler_settings.setmodule(settings)
    # Инициализация процесса, содержащего созданные настройки
    process = CrawlerProcess(settings=crawler_settings)
    # Вызов метода crawl к пауку, здесь можно задать ключевое слово для поиска через keyword=<values>
    process.crawl(LeroySpider, keyword='elektroinstrumenty')
    # Запуск процесса
    process.start()
