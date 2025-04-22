import logging

from requests import RequestException

from exceptions import ParserFindTagException


def get_response(session, url):
    """Перехват ошибки RequestException."""
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}', stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегa."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        message = f'Не найден тег {tag} {attrs}'
        logging.error(message, stack_info=True)
        raise ParserFindTagException(message)
    return searched_tag
