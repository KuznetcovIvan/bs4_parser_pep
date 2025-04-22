import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEPS_URL
from outputs import control_output
from utils import find_next_sibling_tag, find_tag, get_response, select_one_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_section = find_tag(
        soup, 'section', {'id': 'what-s-new-in-python'}
    )
    toctree_wrapper = find_tag(
        main_section, 'div', {'class': 'toctree-wrapper compound'}
    )
    sections_by_python = toctree_wrapper.find_all('li', class_='toctree-l1')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор'), ]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус'), ]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    table = find_tag(soup, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = urljoin(downloads_url, pdf_a4_tag['href'])
    file_name = pdf_a4_link.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / file_name
    response = session.get(pdf_a4_link)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEPS_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    tr_tags = soup.select('tbody tr')[:]
    status_counter = {}
    for tr_tag in tqdm(tr_tags):
        peps_page_statuses = (
            EXPECTED_STATUS[select_one_tag(tr_tag, 'td abbr').text[1:]])
        link = urljoin(PEPS_URL, select_one_tag(tr_tag, 'td a')['href'])
        response = get_response(session, link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        dt_tags = soup.find_all('dt')
        for dt_tag in dt_tags:
            if dt_tag.text == 'Status:':
                pep_page_status = find_next_sibling_tag(dt_tag, 'dd').text
                break
        if pep_page_status not in peps_page_statuses:
            logging.info(
                f'Несовпадающие статусы: {link}\n'
                f'Статус в карточке: {pep_page_status} '
                f'Ожидаемые статусы: {peps_page_statuses}'
            )
        status_counter[pep_page_status] = (
            status_counter.get(pep_page_status, 0) + 1
            )
    status_counter['Total'] = sum(status_counter.values())
    return [
        ('Статус', 'Количество'),
        *[(status, count) for status, count in status_counter.items()]
        ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
