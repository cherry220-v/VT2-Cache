��settings��themeFile�-C:\Users\Trash/Documents/VT2\Themes/style.qss�locale�en�state��splitter��data�   �           	����    �tabWidget��tabBar��movableèclosableéactiveTab�1�tabs��0��name�log.txt�file�$C:/Users/Trash/Documents/VT2/log.txt�canSave��text��
[19:26:53 12 Jan]: Загружен плагин 'Basic'
[19:26:53 12 Jan]: Загружен плагин 'VtDocx'
[19:26:53 12 Jan]: Загружен плагин 'OpenDir'
[19:26:53 12 Jan]: Загружен плагин 'Open&Save'
[19:26:53 12 Jan]: Загружен плагин 'PythonIDE'
[19:26:53 12 Jan]: Загружен плагин 'PythonSyntax'
[19:26:53 12 Jan]: Загружен плагин 'PythonSyntax'
[19:26:53 12 Jan]: Выполнена команда '{'command': 'InitFileTagsCommand', 'kwargs': {'view': }}'
[19:26:53 12 Jan]: Выполнена команда '{'command': 'PythonEditorCommand'}'
[19:26:53 12 Jan]: Выполнена команда '{'command': 'PythonEditorCommand'}'
[19:26:53 12 Jan]: Выполнена команда '{'command': 'OpenFileCommand', 'args': [['log.txt']]}'
[19:27:58 12 Jan]: Выполнена команда '{'command': 'LogConsoleCommand', 'args': None, 'kwargs': None}'�isSavedéselection��0�0�mmapHidden¡1��name�test.py�file�C:\Users\Trash\VT2\test.py�canSave��text��import argparse
import sys

# Создаем парсер для аргументов командной строки
parser = argparse.ArgumentParser(description="VT2 help message.\n--log /path to write log to file.\nargs to open files.")
parser.add_argument('files', nargs='*', help="Список файлов для открытия")
parser.add_argument('--log', type=str, help="Путь к файлу лога", default=None)

# Обрабатываем аргументы
args = parser.parse_args()

# Обрабатываем аргумент с флагом --log
if args.log:
    log_file_path = args.log
    print(f"Лог будет записан в файл: {log_file_path}")
else:
    log_file_path = None
    print("Лог не указан.")

# Пример использования пути к лог-файлу
if log_file_path:
    # Здесь можно открыть лог-файл или передать путь в соответствующий объект для записи лога
    with open(log_file_path, 'a') as log_file:
        log_file.write("Логирование начато...\n")

# Пример открытия файлов (если есть)
if args.files:
    print(args.files)
�isSavedéselection������mmapHidden�