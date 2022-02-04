import subprocess
import paramiko
import time
import os.path
import json
import pathlib
import re

import errno  # для обработки исключений

"""
1) Найти список всех внешних обработок - есть пример. 
2) Запустить конфигуратор в режиме агента - ниже код
3) Выгрузить внешки в файлы
/DumpExternalDataProcessorOrReportToFiles <корневой файл выгрузки> <внешняя обработка (отчет)> [-Format Plain|Hierarchical]

Выполняет выгрузку внешней обработки (отчета) в формате XML. Используется выгрузка формата 2.0 (подробнее см. здесь).

Допустимо использовать следующие параметры:

● <корневой файл выгрузки> ‑ содержит полный путь к корневому каталогу выгрузки. Обязательный параметр.

● <внешняя обработка (отчет)> ‑ полный путь к внешней обработке (отчету) в формате .epf (.erf).

● -Format ‑ указывает формат выгрузки:

● Plain ‑ линейный формат;

● Hierarchical ‑ иерархический формат (по умолчанию).

/LoadExternalDataProcessorOrReportFromFiles <корневой файл выгрузки> <внешняя обработка (отчет)>

Выполняет загрузку внешней обработки (отчета) из формата XML. Используется выгрузка формата 2.0 (подробнее см. здесь).

Допустимо использовать следующие параметры:

● <корневой файл выгрузки> ‑ содержит полный путь к корневому каталогу, который содержит внешнюю обработку (отчет) в файлах формата XML. Обязательный параметр.

● <внешняя обработка (отчет)> ‑ полный путь к внешней обработке (отчету) в формате .epf (.erf), которая получится в результате загрузки. Расширение результирующего файла будет определено автоматически, на основании XML-файлов. Если в командной строке расширение указано неверно ‑ оно будет автоматически заменено на нужное расширение.

4) Найти список строк и вывести на экран
5) поиск в файлах по расширению bsl и глобальный поиск по всем
"""


def timeit(func):
    def wrapper(*args, **kwargs):
        import time

        start = time.time()
        return_value = func(*args, *kwargs)
        end = time.time()
        print('[*] Время выполнения: {}: {} секунд.'.format(func.__name__, end - start))

        return return_value

    return wrapper


class ConnectTo1c:
    # Private
    __process = None  # процесс конфигуратора 1с
    __DesignerStarted = False  # флаг запуска конфигуратора 1с

    __SSHСlient = None  # SSH подключение
    __SSHСhannel = None  # SSH канал
    __SSHEnabled = False  # SSH флаг

    # For edit
    path_platform_1c = ""  # путь к платформе 1с например C:\Program Files\1cv8\8.3.17.1549\bin\1cv8.exe
    path_filebase_1c = ""  # путь к базе, конфигуратор которой откроется
    dirforfiles_1c = ""  # путь к каталогу с внешними обработками
    dirforxmlfiles_from1c = ""  # путь к каталогу куда выгрузить внешние обработки

    address_server_1c = ""  # Сервер 1с localhost:2640
    name_infobase_1c = ""  # Имя информационной базы

    username_1c = ""  # Пользователь 1с
    secret_1c = ""  # пароль 1с

    host = r'127.0.0.1'  # адрес, где запустится конфигуратор как агент. К нему будет подключение по SSH для послания команд
    user = r''  # логин для подключения по SSH
    secret = r''  # пароль для подключения по SSH
    port = 1543  # порт для подключения по SSH

    printlog = False

    def __init__(self, path_platform_1c: str, path_filebase_1c: str, dirforfiles_1c: str, address_server_1c: str = '',
                 name_infobase_1c: str = '', username_1c: str = '', secret_1c: str = '') -> object:  # Инициализатор

        if not os.path.exists(path_platform_1c):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path_platform_1c)
        else:
            self.path_platform_1c = path_platform_1c

        if path_filebase_1c:
            if not os.path.exists(path_filebase_1c):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path_filebase_1c)
            else:
                self.path_filebase_1c = path_filebase_1c

        self.address_server_1c = address_server_1c
        self.name_infobase_1c = name_infobase_1c
        self.username_1c = username_1c
        self.secret_1c = secret_1c
        self.dirforfiles_1c = dirforfiles_1c

    def __del__(self):  # Деструктор
        self.Close1cDesigner()
        self.CloseConnection()

    def start1cDesigner(self):

        if not os.path.exists(self.path_platform_1c):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.path_platform_1c)

        param_username_1c = '/N ' + self.username_1c
        param_secret_1c = '/P ' + self.secret_1c

        param_base_1c = ''
        if self.path_filebase_1c:
            if not os.path.exists(self.path_filebase_1c):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.path_filebase_1c)
            param_base_1c = '/F ' + self.path_filebase_1c
        elif self.address_server_1c and self.name_infobase_1c:
            param_base_1c = '/S ' + self.address_server_1c + r'\\' + self.name_infobase_1c
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.path_filebase_1c)

        param_dirforfiles = "/AgentBaseDir " + self.dirforfiles_1c

        self.Close1cDesigner()

        self.__process = subprocess.Popen([
            self.path_platform_1c,
            r'DESIGNER',
            param_base_1c,
            param_username_1c,
            param_secret_1c,
            r'/AgentMode',
            r'/AgentSSHHostKeyAuto',
            param_dirforfiles,
            r'/Visible'])

        self.__DesignerStarted = True

        print('Запущен конфигуратор')

    def Close1cDesigner(self):

        if self.__DesignerStarted or self.__process:
            self.exec_command('disconnect-ib')
            self.exec_command('shutdown')

            self.__process.kill()

            self.__process = None
            self.__DesignerStarted = False

            print('Конфигуратор закрыт')

    def IsStartedDesigner(self):
        return self.__DesignerStarted and self.__process

    def ConnectSSHTo1c(self):

        if not self.IsStartedDesigner():
            self.start1cDesigner()

        done = False
        for i in range(5):
            time.sleep(2)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(hostname=self.host, port=self.port, username=self.user, password=self.secret)
                done = True
            except:
                print('Попытка №{}: '.format(i + 1))

        if not done:
            print('Не удалось подключиться к Агенту конфигуратора по SSH: ')
            return None

        self.__SSHСlient = client

        transport = client.get_transport()

        channel = transport.open_session()

        self.__SSHСhannel = channel
        self.__SSHEnabled = True

        channel.invoke_shell()

        print(channel.recv(5000).decode('utf-8'))

        self.exec_command('options set --show-prompt=no')
        self.exec_command('options set --output-format=json')

        self.exec_command('common connect-ib')

        print('Подключение к базе: ' + channel.recv(5000).decode('utf-8'))

    def CloseConnection(self):

        if self.__SSHEnabled or self.__SSHСhannel:
            self.exec_command('common disconnect-ib')
            time.sleep(1)
            print('Отключение от базы: ' + self.__SSHСhannel.recv(5000).decode('utf-8'))

            self.exec_command('common shutdown')
            time.sleep(1)
            print('Завершение работы: ' + self.__SSHСhannel.recv(5000).decode('utf-8'))

            self.__SSHСhannel.close()

            self.__SSHСlient.close()

            self.__SSHСlient = None
            self.__SSHСhannel = None
            self.__SSHEnabled = False

    def IsConnectSSHStarted(self):
        return self.__SSHEnabled

    def exec_command(self, command: str):
        if self.__SSHEnabled:
            # self.__SSHСhannel.send('common connect-ib' + '\n')
            time.sleep(0.5)
            self.__SSHСhannel.send(command + '\n')
            if self.printlog:
                print(self.__SSHСhannel.recv(5000).decode('utf-8'))


@timeit
def getallfiles(dir):
    ExternalReportFiles = pathlib.Path(dir).rglob(r'**\*.erf')

    ExternalReports = []

    for file in ExternalReportFiles:
        ExternalReports.append(file)

    ExternalDataProcessorFiles = pathlib.Path(dir).rglob(r'**\*.epf')

    ExternalDataProcessor = []

    for file in ExternalDataProcessorFiles:
        ExternalDataProcessor.append(file)

    return ExternalReports, ExternalDataProcessor


@timeit
def DumpExternalDataProcessorOrReportToFiles(connect, dirforfiles):
    files = getallfiles(dirforfiles)
    for anytype in files:
        for er in anytype:
            if connect.dirforxmlfiles_from1c:
                newxmlfile = str(pathlib.Path(connect.dirforxmlfiles_from1c, er.stem + '.xml'))
                connect.exec_command(
                    'config dump-external-data-processor-or-report-to-files --file ' + newxmlfile + ' --ext-file ' + str(
                        er))
            else:
                newxmlfile = str(pathlib.Path(er.parent, '_unloadfiles', er.stem + '.xml'))
                connect.exec_command(
                    'config dump-external-data-processor-or-report-to-files --file ' + newxmlfile + ' --ext-file ' + str(
                        er))


@timeit
def showtext(path, filter, FP):
    if FP:
        pattern = re.escape(filter)
    else:
        pattern = r'(.*$filter.*)'

        if filter:
            filter = re.escape(filter)
            pattern = pattern.replace('$filter', filter)

    # Получили файлы
    dict_file = getAllFilesByPattern(path, pattern)

    return dict_file


def printeventlist(textlist, key):
    eventlist = textlist[key]
    for i in eventlist:
        print(' {}'.format(i))


def getAllFilesByPattern(dir, pattern):
    dict_file = {}

    exts = ['bsl', 'xml']
    for ext in exts:
        logfiles = pathlib.Path(dir).rglob(r'**\*.' + ext)

        for fileName in logfiles:
            filetext = fileName.read_text(encoding='utf-8-sig', errors='ignore')
            allMatch = re.findall(pattern, filetext)
            if allMatch:
                for match in allMatch:
                    keyFile = str(fileName)
                    if not keyFile in dict_file.keys():
                        dict_file[keyFile] = []
                    dict_file[keyFile].append(re.sub('\s+', " ", match))

    return dict_file


if __name__ == "__main__":

    platform_1c: str = r'C:\Program Files\1cv8\8.3.18.1483\bin\1cv8.exe'
    # base_1c = r'C:\Users\d.vasilev\Documents\ПустаяБаза'
    base_1c = None
    dirforfiles = r'C:\Users\d.vasilev\Desktop\ВыгрузкаВнешнихФайлов'

    address_server_1c = r'sam-srv-hp1:2641'
    name_infobase_1c = r'tester_1c'

    connect = ConnectTo1c(platform_1c, base_1c, dirforfiles, address_server_1c, name_infobase_1c)

    while True:
        comandtosearch = input('Введи команду\n')
        if comandtosearch.upper() == 'END':
            print('good bye')
            break
        elif comandtosearch.upper() == 'CT1C'.upper():
            connect = None
            connect = ConnectTo1c(platform_1c, base_1c, dirforfiles, address_server_1c, name_infobase_1c)
            connect.ConnectSSHTo1c()
        elif comandtosearch.upper() == 'DUMP':
            if connect.IsConnectSSHStarted():
                DumpExternalDataProcessorOrReportToFiles(connect, dirforfiles)
        elif comandtosearch.upper() == 'FF'.upper() or comandtosearch.upper() == 'FP'.upper():
            FP = False
            if comandtosearch.upper() == 'FF'.upper():
                textToSearch = input('Введи текст для поиска\n')
            elif comandtosearch.upper() == 'FP'.upper():
                textToSearch = input('Введи патерн для поиска\n')
                FP = True

            if textToSearch:
                if connect.dirforxmlfiles_from1c:
                    path_dir = pathlib.Path(connect.dirforxmlfiles_from1c)
                else:
                    path_dir = pathlib.Path(dirforfiles)

                textlist = showtext(path_dir, textToSearch, FP)

                for f in textlist.keys():
                    print('В файла {}:'.format(f))
                    printeventlist(textlist, f)
        else:
            print('Press end to stop')








