from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
import re
from pymongo import MongoClient


def date_conversion(date_):
    """
    Обрабатывает дату, содержащую значение «Сегодня» или «Вчера» -- заменят их соответствующими значениями числа и
    месяца.
    С помощью datetime.now() получается значение сегодняшних или вчерашних числа и месяца.
    С помщью re.match() удаляется «0» из значений типа «01», «02», etc.
    (re.match ищет символы, соответствующие шаблону, в начале строки, указанной в параметрах метода)
    Числовое значение месяца заменяется на текстовое с помощью словаря months

    :param date_: значение даты типа str.
    :return: преобразованная дата типа str.
    """
    months = {'01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля', '05': 'мая', '06': 'июня',
              '07': 'июля', '08': 'августа', '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'
              }
    if 'Сегодня' in date_:
        today_day = datetime.now().strftime('%d')
        if re.match(r'[0]', today_day):
            today_day = today_day.replace('0', '')
        today_month = months[datetime.now().strftime('%m')]
        return date_.replace('Сегодня', f'{today_day} {today_month}')
    else:
        yesterday_day = (datetime.now() - timedelta(days=1)).strftime('%d')
        if re.match(r'[0]', yesterday_day):
            yesterday_day = yesterday_day.replace('0', '')
        yesterday_month = months[(datetime.now() - timedelta(days=1)).strftime('%m')]
        return date_.replace('Вчера', f'{yesterday_day} {yesterday_month}')


class MailRuParser:
    def __init__(self, login_, password_, visibility_, test_emails_count_):
        """
        Создаёт объект класса MailRuParser, к которому применются функции по сбору информации.

        :param login_: логин на сайте mail.ru.
        :param password_: пароль на сайте mail.ru.
        :param visibility_: опция для отображения браузера.
        :param test_emails_count_: число создаваемых тестовых писем для заполнения почтового ящика. Если «0», то
        создание тестовых писем не производится.
        """
        # Логин и пароль
        self.login = login_
        self.password = password_
        # Если передано значение «y», то отображение браузера
        if visibility_ == 'y':
            self.driver = webdriver.Chrome('./chromedriver.exe')
        # Если передано значение «n», то браузер не отображается
        else:
            options = Options()
            options.add_argument('--headless')
            self.driver = webdriver.Chrome('./chromedriver.exe', options=options)
        # Установка ожидания загрузки элементов в 30 секунд
        self.wait = WebDriverWait(self.driver, 30)
        # Число создаваемых тестовых писем, если «0», то письма не создаются
        self.test_emails_count = test_emails_count_
        # Список для сбора данных, полученных при прочтении писем
        self.data = []

    def authorization(self):
        """Авторизация на сайте mail.ru"""
        login_page = 'https://mail.ru/'
        self.driver.get(login_page)
        # Определение методов поиска и путей к элементам страницы
        save_auth_locator = By.NAME, 'saveauth'
        login_locator = By.NAME, 'login'
        password_locator = By.NAME, 'password'
        # Ожидание элемента «запомнить» и снятие соответствующей отметки, если она поставлена
        self.wait.until(EC.element_to_be_clickable(save_auth_locator))
        saveauth_checkbox = self.driver.find_element(*save_auth_locator)
        if saveauth_checkbox.is_selected():
            saveauth_checkbox.click()
        # Ввод и отправка логина
        login_window = self.driver.find_element(*login_locator)
        login_window.send_keys(self.login)
        login_window.send_keys(Keys.RETURN)
        # Ожидание элемента «Ввести пароль»
        self.wait.until(EC.element_to_be_clickable(password_locator))
        # Ввод и отправка пароля
        password_window = self.driver.find_element(*password_locator)
        password_window.send_keys(self.password)
        password_window.send_keys(Keys.RETURN)

    def filling_mailbox(self, num_):
        """
        Создание тестового письма для наполнения почтового ящика (письмо отправляется самому себе).
        В поле «Тема» и текстовое поле вписывается значения типа «Тестовое письмо num_».

        :param num_: числовое значение, которое будет добавлено в поля «Тема» и «Текст».
        Поступает из цикла for i in range() поэтому требует увеличения на единицу.
        :return: ничего; отправлет тестовое письмо
        """
        num_ += 1
        # Определение методов поиска и путей к элементам страницы
        letter_writing_locator = By.CSS_SELECTOR, 'a.compose-button'
        to_whom_locator = By.CSS_SELECTOR, 'input[tabindex="100"]'
        theme_locator = By.CSS_SELECTOR, 'input[tabindex="400"]'
        text_area_locator = By.CSS_SELECTOR, 'div[tabindex="505"]'
        send_button_locator = By.CSS_SELECTOR, 'span[tabindex="570"]'
        close_button_locator = By.CSS_SELECTOR, 'span[tabindex="1000"]'
        # Ожидание элемента «Написать письмо» и нажатие на него
        self.wait.until(EC.element_to_be_clickable(letter_writing_locator))
        letter_writing_button = self.driver.find_element(*letter_writing_locator)
        letter_writing_button.click()
        # Ожидание поля «От кого»
        self.wait.until(EC.element_to_be_clickable(to_whom_locator))
        # Заполнение поля «От кого»
        to_whom = self.driver.find_element(*to_whom_locator)
        to_whom.send_keys(f'{self.login}@mail.ru')
        # Заполнение поля «Тема»
        theme = self.driver.find_element(*theme_locator)
        theme.send_keys(f'Тестовое письмо {num_}')
        # Заполнение тектового поля
        text_area = self.driver.find_element(*text_area_locator)
        text_area.send_keys(f'Тестовое письмо {num_}')
        # Нажатие на кнопку «Отправить»
        send_button = self.driver.find_element(*send_button_locator)
        send_button.send_keys(Keys.RETURN)
        # Ожидание кнопки «Закрыть»
        self.wait.until(EC.element_to_be_clickable(close_button_locator))
        # Нажатие на кнопку «Закрыть»
        close_button = self.driver.find_element(*close_button_locator)
        close_button.click()

    def get_links(self):
        """
        Собирает ссылки на письма в динамическом окне mail.ru.

        :return: список собранных ссылок.
        """
        # Определение методов поиска и путей к элементам страницы
        link_path_locator = By.CSS_SELECTOR, 'a.js-tooltip-direction_letter-bottom'
        # Ожидание прогрузки динамического окна (несколько условий для повышения стабильности)
        self.wait.until(EC.visibility_of_all_elements_located(link_path_locator))
        self.wait.until(EC.element_to_be_clickable(link_path_locator))
        # Получение ссылок из текущего окна
        current_links = [link.get_attribute('href') for link in self.driver.find_elements(*link_path_locator)]
        # Создание контрольного списка ссылок
        previous_links = current_links
        # Инициализация общего списка ссылок и включение в него уже собранных ссылок
        links = current_links
        # Скроллинг динамического окна
        while True:
            # Имитация команды PAGE_DOWN применительно к последнему письму в динамическом окне
            self.driver.find_elements(*link_path_locator)[-1].send_keys(Keys.PAGE_DOWN)
            # Ожидание прогрузки динамического окна (несколько условий для повышения стабильности)
            self.wait.until(EC.visibility_of_all_elements_located(link_path_locator))
            self.wait.until(EC.element_to_be_clickable(link_path_locator))
            # Получение ссылок из текущего окна
            current_links = [link.get_attribute('href') for link in self.driver.find_elements(*link_path_locator)]
            # Если новые ссылки отличаются от собранных во время предыдущей итерации (т. е. от контрольного списка)
            if current_links != previous_links:
                links += current_links
                # Обновление контрольного списка и передача в общий список
                previous_links = current_links
            # Если новые ссылки такие же, как и при предыдущей итерации, то конец страницы достигнут, выход из цикла
            else:
                break
        # Удаление повторяющихся ссылок и возврат списка
        links = list(set(links))
        print(f'Получено писем: {len(links)}')
        return links

    def mail_parse(self, link):
        """
        Сбор информации из письма

        :param link: ссылка на письмо
        :return: добавляет собранную информацию в список self.data для дальнейшей передачи в БД PyMongo
        """
        # Обращение к странице с письмом
        self.driver.get(link)
        # Определение методов поиска и путей к элементам страницы
        sender_locator = By.CSS_SELECTOR, 'span.letter-contact'
        date_locator = By.CSS_SELECTOR, 'div.letter__date'
        subject_locator = By.CSS_SELECTOR, 'h2.thread__subject.thread__subject_pony-mode'
        text_locator = By.CSS_SELECTOR, 'div.js-helper.js-readmsg-msg div div div div'
        signature_locator = By.CSS_SELECTOR, 'div[data-signature-widget="content"]'
        # Ожидание прогрузки элементов
        self.wait.until(EC.element_to_be_clickable(sender_locator))
        # От кого
        sender_name = self.driver.find_element(*sender_locator).text
        sender_email = self.driver.find_element(*sender_locator).get_attribute('title')
        sender = f'{sender_name} <{sender_email}>'
        # Дата отправки
        date = self.driver.find_element(*date_locator).text
        if 'Сегодня' or 'Вчера' in date:
            date = date_conversion(date)
        # Тема письма
        subject = self.driver.find_element(*subject_locator).text
        # Текст письма
        try:
            text = self.driver.find_element(*text_locator).text
            # Если текстовое поле пустое
            if text == '':
                text = 'Без текста, или содержимое представляет собой динамический элемент'
        # Если текстовое поле отсутствует
        except NoSuchElementException:
            text = 'Без текста, или содержимое представляет собой динамический элемент'
        # Подпись
        try:
            signature = self.driver.find_element(*signature_locator).text
        # Если поле с подписью отсутствует
        except NoSuchElementException:
            signature = 'Без подписи'
        # Передача собранных данных в список self.data для дальнейшей передачи в БД PyMongo
        self.data.append(
            {
                'sender': sender,
                'date': date,
                'subject': subject,
                'text': text,
                'signature': signature
            }
        )

    def data_to_db(self):
        """Создаёт базу данных из информации, собранной при чтении писем"""
        # Имя базы данных
        db_name = 'MailRuDB'
        # Имя коллекции
        collection_name = 'IncomingMail'
        # Создание клиента для подключения к серверу
        client = MongoClient('localhost', 27017)
        # Подключение к БД
        db = client[db_name]
        # Создание указателя на коллекцию, чтобы было проще проще обращаться к ней
        collection = db[collection_name]
        # Вставка данных
        collection.insert_many(self.data)

    def run(self):
        # Авторизация
        self.authorization()
        # Сохдание и отправка тестовых писем в случае, если их чило больше ноля
        if self.test_emails_count != 0:
            for i in range(self.test_emails_count):
                self.filling_mailbox(i)
        # Получение ссылок на письма
        links = self.get_links()
        # Чтение писем
        for num, link in enumerate(links):
            print(f'Обработка письма {num + 1} из {len(links)}')
            self.mail_parse(link)
        # Передача собранных данных в базу данных MongoDB
        self.data_to_db()
        # Завершение работы драйвера
        self.driver.close()


# Ввод логина и пароля для почтового ящика mail.ru
login = input('Введите логин от почтового ящика mail.ru: ')
password = input('Введите пароль от почтового ящика mail.ru: ')
# Опция отображения работы браузера
visibility = input('Включить демонстрацию браузера? (y/n): ')
# Опция наполнения ящика тестовыми письмами
test_emails_count = int(
    input('Наполнить почтовый ящик тестовыми письмами? Если да — введите число писем, если нет — введите «0»: ')
)
#
# Инициализция объекта класса MailRuParser
mail_parser = MailRuParser(login, password, visibility, test_emails_count)
# Запуск объекта
mail_parser.run()
