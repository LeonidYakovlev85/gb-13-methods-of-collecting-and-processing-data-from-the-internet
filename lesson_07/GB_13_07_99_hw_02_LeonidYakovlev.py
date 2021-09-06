from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from pymongo import MongoClient


class QueenParser:
    def __init__(self, visibility_):
        self.base_page = 'https://genius.com/artists/Queen'
        # Если передано значение «y», то отображение браузера
        if visibility_ == 'y':
            self.driver = webdriver.Chrome('./chromedriver.exe')
        # Если передано значение «n», то браузер не отображается
        else:
            options = Options()
            options.add_argument('--headless')
            self.driver = webdriver.Chrome('./chromedriver.exe', options=options)
        # Установка ожидания загрузки элементов в 30 секунд
        self.wait = WebDriverWait(self.driver, 10)
        # Список для сбора данных, полученных песен
        self.data = []

    def get_songs(self):
        """
        Собирает ссылки на песни в динамическом окне.

        :return: список собранных ссылок.
        """
        # Переход на страницу
        self.driver.get(self.base_page)
        show_all_songs_locator = By.XPATH, '//div[normalize-space()="Show all songs by Queen"]'
        # Ожидание загрузки элементов
        self.wait.until(EC.visibility_of_element_located(show_all_songs_locator))
        # Нажатие на элемент «Show all songs by Queen»
        self.driver.find_element(*show_all_songs_locator).click()
        # Определение методов поиска и путей к элементам страницы
        song_locator = By.CSS_SELECTOR, 'a.mini_card.mini_card--small'
        # Ожидание загрузки элементов
        self.wait.until(EC.visibility_of_element_located(song_locator))
        # Текущее число отображаемых песен
        collected_links_len = len(self.driver.find_elements(*song_locator))
        # Прокрутка динамического окна с песнями -- подгрузка динамического окна до тех пор, пока это возможно
        while True:
            # Нажатие клавиши «END» применительно к первой песне
            self.driver.find_element(*song_locator).send_keys(Keys.END)
            # Получение ссылок на песни и, если их число больше, чем число собранных, то
            # уточнение числа собранных ссылок и прокрутка дальше
            try:
                self.wait.until(lambda x: len(self.driver.find_elements(*song_locator)) > collected_links_len)
                collected_links_len = len(self.driver.find_elements(*song_locator))
            # Если число ссылок на песни на странице не больше, чем собранного, то конец страницы достигнут,
            # сбор всех ссылок и выход из цикла
            except TimeoutException:
                break
        # Сбор ссылок
        return [song.get_attribute('href') for song in self.driver.find_elements(*song_locator)]

    def song_parse(self, link_):
        """
        Сбор информации о песне

        :param link_: ссылка на песню
        :return: добавляет собранную информацию в список self.data для дальнейшей передачи в БД PyMongo
        """
        # Обращение к странице с песней
        self.driver.get(link_)
        # Определение методов поиска и путей к элементам страницы
        singer_locator = By.CSS_SELECTOR, 'a.header_with_cover_art-primary_info-primary_artist'
        title_locator = By.CSS_SELECTOR, 'h1.header_with_cover_art-primary_info-title'
        # Ожидание загрузки элементов
        self.wait.until(EC.visibility_of_element_located(singer_locator))
        # Исполнитель
        singer = self.driver.find_element(*singer_locator).text
        # Название
        title = self.driver.find_element(*title_locator).text
        # Передача собранных данных в список self.data для дальнейшей передачи в БД PyMongo
        self.data.append(
            {
                'singer': singer,
                'title': title
            }
        )

    def data_to_db(self):
        """Создаёт базу данных из информации о песне"""
        # Имя базы данных
        db_name = 'QueenDB'
        # Имя коллекции
        collection_name = 'QueenSongs'
        # Создание клиента для подключения к серверу
        client = MongoClient('localhost', 27017)
        # Подключение к БД
        db = client[db_name]
        # Создание указателя на коллекцию, чтобы было проще проще обращаться к ней
        collection = db[collection_name]
        # Вставка данных
        collection.insert_many(self.data)

    def run(self):
        # Получение списка ссылок на псени
        links = self.get_songs()
        print(f'Найдено песен: {len(links)}')
        # Обход страниц со ссылками
        for num, link in enumerate(links[:5]):
            print(f'Обработка песни {num + 1} из {len(links)}')
            self.song_parse(link)
        # Передача собранных данных в базу данных MongoDB
        self.data_to_db()
        # Завершение работы драйвера
        self.driver.close()


# Опция отображения работы браузера
visibility = input('Включить демонстрацию браузера? (y/n): ')
queen_parser = QueenParser(visibility)
queen_parser.run()
