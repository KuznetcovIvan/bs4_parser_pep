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


def handle_tag_result(searched_tag, message):
    """Обработка результата поиска тега."""
    if searched_tag is None:
        logging.error(message, stack_info=True)
        raise ParserFindTagException(message)
    return searched_tag


def find_tag(soup, tag, attrs=None, string=None):
    """Перехват ошибки поиска тега с использованием find."""
    message = f'Не найден тег <{tag}>'
    if attrs is not None:
        message += f'c атрибутами {attrs}'
    if string is not None:
        message += f' со строкой "{string}"'
    return handle_tag_result(
        soup.find(tag, attrs=(attrs or {}), string=string), message
    )


def select_one_tag(soup, selector):
    """Перехват ошибки поиска тега с использованием select_one."""
    return handle_tag_result(
        soup.select_one(selector), f'Не найден тег по селектору {selector}'
    )


def find_next_sibling_tag(tag, sibling_tag):
    """Перехват ошибки, если следующий тег не найден."""
    return handle_tag_result(
        tag.find_next_sibling(sibling_tag),
        f'После тега <{tag.name}> нет тега <{sibling_tag}>'
    )
