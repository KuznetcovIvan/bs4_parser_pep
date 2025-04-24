import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, FILE_OUTPUT, PRETTY_OUTPUT,
                       RESULTS_DIR_NAME)

FILE_SAVED_MESSAGE = 'Файл с результатами был сохранён: {}'


def pretty_output(results, *args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, *args):
    results_dir = BASE_DIR / RESULTS_DIR_NAME
    results_dir.mkdir(exist_ok=True)
    file_path = (
        results_dir /
        f'{args[0].mode}_{dt.datetime.now().strftime(DATETIME_FORMAT)}.csv'
    )
    with open(file_path, 'w', encoding='utf-8') as file:
        csv.writer(file, dialect=csv.unix_dialect).writerows(results)
    logging.info(FILE_SAVED_MESSAGE.format(file_path))


def default_output(results, *args):
    for row in results:
        print(*row)


OUTPUT_TO_FUNCTIONS = {
    PRETTY_OUTPUT: pretty_output,
    FILE_OUTPUT: file_output,
    None: default_output
}


def control_output(results, cli_args):
    OUTPUT_TO_FUNCTIONS.get(cli_args.output)(results, cli_args)
