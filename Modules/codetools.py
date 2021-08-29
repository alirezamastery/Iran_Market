from persiantools.jdatetime import JalaliDate
import inspect


def list_printer_horizontal(names, space: int = 20, columns: int = 3, separator: str = ' ', bullet: str = '.',
                            indentor: str = '    '):
    if columns < 1:
        raise RuntimeError('columns can not be smaller than 1')
    indent = len(str(len(names)))
    while True:
        if len(names) % columns != 0:
            names.append('')
        else:
            break
    cols = list()
    for i in range(columns):
        cols.append(names[i::columns])

    for i, row in enumerate(zip(*cols)):
        line_format = list()
        for j, value in enumerate(row):
            line_format.append(f'{i * columns + j + 1:>{indent}}{bullet}{value:<{space}}' if value != '' else '')
        print(f'{indentor}{f"{separator}".join(line_format)}')


def list_printer_vertical(names, space: int = 20, columns: int = 3, separator: str = ' ', bullet: str = '.',
                          indentor: str = '    '):
    if columns < 1:
        raise RuntimeError('columns can not be smaller than 1')
    indent = len(str(len(names)))
    while True:
        if len(names) % columns != 0:
            names.append('')
        else:
            break
    pivot = len(names) // columns
    cols = list()
    for i in range(columns):
        if i == columns - 1:
            cols.append(names[pivot * (columns - 1):])
        else:
            cols.append(names[pivot * i:pivot * (i + 1)])

    for i, row in enumerate(zip(*cols)):
        line_format = list()
        for j, value in enumerate(row):
            line_format.append(f'{i + pivot * j + 1:>{indent}}{bullet}{value:<{space}}' if value != '' else '')
        print(f'{indentor}{f"{separator}".join(line_format)}')


def jalali_to_gregorian(date: str):
    """input format: YYYY-MM-DD"""
    return str(JalaliDate(int(date[:4]), int(date[5:7]), int(date[-2:])).to_gregorian())


def gregorian_to_jalali(date: str):
    """input format: YYYY-MM-DD"""
    return str(JalaliDate.to_jalali(int(date[:4]), int(date[5:7]), int(date[-2:])))


def log(*args: str, blank_lines: int = 0, caller_name: bool = False):
    for _ in range(blank_lines):
        print('\n')
    if caller_name:
        caller = inspect.stack()[1].function
        print(f'{caller}:', *args)
    else:
        print(*args)
