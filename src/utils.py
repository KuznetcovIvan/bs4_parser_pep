import requests
from bs4 import BeautifulSoup

from exceptions import ParserFindTagException

GET_RESPONSE_MESSAGE = 'Возникла ошибка при загрузке страницы {} {}'
FIND_TAG_MESSAGE = 'Не найден тег {} {}'
ADD_FIND_TAG_MESSAGE = ' cо строкой \'{}\''
FIND_NEXT_SIBLING_MESSAGE = 'После тега {} нет тега {}'


def get_response(session, url, encoding='utf-8'):
    """Перехват ошибки RequestException."""
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except requests.RequestException as error:
        raise ConnectionError(
            GET_RESPONSE_MESSAGE.format(url, error))


def handle_tag_result(searched_tag, message):
    """Обработка результата поиска тега."""
    if searched_tag is None:
        raise ParserFindTagException(message)
    return searched_tag


def find_tag(soup, tag, attrs=None, string=''):
    """Поиск тега с использованием find.
    Бросает исключение, если не найден."""
    message = FIND_TAG_MESSAGE.format(tag, attrs)
    if string:
        message += ADD_FIND_TAG_MESSAGE.format(string)
    return handle_tag_result(
        soup.find(tag, attrs={} if attrs is None else attrs, string=string),
        message
    )


def find_next_sibling_tag(tag, sibling_tag):
    """Поиск следующего тега с использованием find_next_sibling.
    Бросает исключение, если не найден."""
    return handle_tag_result(
        tag.find_next_sibling(sibling_tag),
        FIND_NEXT_SIBLING_MESSAGE.format(tag.name, sibling_tag)
    )


def get_soup(session, url, features='lxml'):
    """Возвращает объект BeautifulSoup для переданного URL"""
    return BeautifulSoup(get_response(session, url).text, features=features)
