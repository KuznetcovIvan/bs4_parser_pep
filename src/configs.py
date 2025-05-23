import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import FILE_OUTPUT, LOG_DIR, LOG_FILE, PRETTY_OUTPUT

LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
DESCRIPTION = 'Парсер документации Python'
MODE_HELP = 'Режимы работы парсера'
CLEAR_CACHE_HELP = 'Очистка кеша'
OUTPUT_HELP = 'Дополнительные способы вывода данных'


def configure_argument_parser(available_models):
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        'mode',
        choices=available_models,
        help=MODE_HELP
        )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help=CLEAR_CACHE_HELP
        )
    parser.add_argument(
        '-o',
        '--output',
        choices=(PRETTY_OUTPUT, FILE_OUTPUT), help=OUTPUT_HELP
        )
    return parser


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10**6, backupCount=5, encoding='utf-8'
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler()),
        encoding='utf-8'
    )
