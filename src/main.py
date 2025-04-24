import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEPS_URL
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_next_sibling_tag, find_tag, get_response

GET_SOUP_MESSAGE = 'Не удалось загрузить страницу: {}'
LATEST_VERSIONS_MESSAGE = (
    'Не найден тег <ul> c текстом {} на странице: {}'
)
DOWNLOAD_MESSAGE = 'Архив был загружен и сохранён: {}'
PEP_TQDM_MESSAGE = 'Парсим статусы PEP'
PEP_MESSAGE = (
    'Несовпадающие статусы: {}\n'
    'Статус в карточке: {} '
    'Ожидаемые статусы: {}'
)
START_MESSAGE = 'Парсер запущен!'
END_MESSAGE = 'Парсер завершил работу.'
ERROR_MESSAGE = 'Ошибка в работе парсера: {}'
ARGS_MESSAGE = 'Аргументы командной строки: {}'
WHATS_NEW_RESULTS = ('Ссылка на статью', 'Заголовок', 'Редактор, автор')
LATEST_VERSIONS_RESULTS = ('Ссылка на документацию', 'Версия', 'Статус')
PEP_RESULTS = ('Статус', 'Количество')
TOTAL_PEP = 'Итого'


def get_soup(session, url, features='lxml'):
    """Возвращает объект BeautifulSoup для переданного URL"""
    response = get_response(session, url)
    if response is None:
        logging.warning(GET_SOUP_MESSAGE.format(url))
        return
    return BeautifulSoup(response.text, features=features)


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    sections_by_python = get_soup(session, whats_new_url).select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )
    results = [WHATS_NEW_RESULTS]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        soup = get_soup(session, version_link)
    results.append((
        version_link,
        find_tag(soup, 'h1').text,
        find_tag(soup, 'dl').text.replace('\n', ' ')
    ))
    return results


def latest_versions(session):
    ul_tags = (
        get_soup(session, MAIN_DOC_URL).select('div.sphinxsidebarwrapper ul')
    )
    search_text = 'All versions'
    for ul in ul_tags:
        if search_text in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException(
            LATEST_VERSIONS_MESSAGE.format(search_text, MAIN_DOC_URL)
        )
    results = [LATEST_VERSIONS_RESULTS]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((a_tag['href'], version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    table = find_tag(
        get_soup(session, downloads_url), 'table', {'class': 'docutils'}
    )
    pdf_a4_tag = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = urljoin(downloads_url, pdf_a4_tag['href'])
    file_name = pdf_a4_link.split('/')[-1]
    # Тесты падают при переносе BASE_DIR / 'downloads' в constants.py.
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / file_name
    response = session.get(pdf_a4_link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_MESSAGE.format(archive_path))


def pep(session):
    status_counter = defaultdict(int)
    logging_message = []
    for tr_tag in tqdm(
        [
            tr for tr in get_soup(session, PEPS_URL).find_all('tr')
            if tr.find_parent(
                'table', class_='pep-zero-table docutils align-default'
            )
        ],
        desc=PEP_TQDM_MESSAGE
    ):
        if tr_tag.find('th') is not None:
            continue
        link = urljoin(PEPS_URL, find_tag(tr_tag, 'a')['href'])
        td_tag = find_tag(tr_tag, 'td')
        peps_page_statuses = td_tag.text[1:]
        for dt_tag in get_soup(session, link).find_all('dt'):
            if dt_tag.text == 'Status:':
                pep_page_status = find_next_sibling_tag(dt_tag, 'dd').text
                break
        expected_status = EXPECTED_STATUS[peps_page_statuses]
        if pep_page_status not in expected_status:
            logging_message.append(
                PEP_MESSAGE.format(link, pep_page_status, expected_status)
            )
        status_counter[pep_page_status] += 1
    for message in logging_message:
        logging.info(message)
    sorted_status_counter = dict(sorted(status_counter.items()))
    return [
        PEP_RESULTS,
        *[(status, count) for status, count in sorted_status_counter.items()],
        (TOTAL_PEP, sum(sorted_status_counter.values()))
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(START_MESSAGE)
    try:
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(ARGS_MESSAGE.format(args))
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as error:
        logging.exception(ERROR_MESSAGE.format(error), stack_info=True)
    finally:
        logging.info(END_MESSAGE)


if __name__ == '__main__':
    main()
