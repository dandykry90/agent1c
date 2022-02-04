from enum import Enum
from abc import ABC, abstractmethod


class InfobaseType(Enum):
    FILEBASE = 1
    SERVER = 2


class InfoBase:
    info_base_type = None

    def __init__(self, *, infobase_type: InfobaseType,
                 path_file_base: str, address_server: str = '', name_infobase: str = ''):

        self.infobase_type = infobase_type

        if infobase_type == InfobaseType.SERVER:
            self.name_infobase = name_infobase
            self.address_server = address_server
        elif infobase_type == InfobaseType.FILEBASE:
            self.path_file_base = path_file_base

    def get_parametrs(self):
        if self.infobase_type == InfobaseType.SERVER:
            return r'/S ' + self.address_server + r'\\' + self.name_infobase
        elif self.infobase_type == InfobaseType.FILEBASE:
            return r'/F ' + self.path_file_base


class AgentType(Enum):
    ENTERPRISE = "ENTERPRISE"
    DESIGNER = "DESIGNER"

    def __str__(self):
        pass


def known_parametrs():

    return []


class ConnectionStringCreater:

    ConnectionString = ""

    infobase = None

    username_1c = ""
    secret_1c = ""

    additional_params = None

    agent_mode = True
    AgentSSHHostKeyAuto = True
    AgentBaseDir = ""

    def __init__(self, *, infobase: InfoBase, agent_type: AgentType,
                 username_1c="", secret_1c="", additional_params: tuple):

        self.infobase = infobase
        self.agent_type = agent_type

        self.username_1c = username_1c
        self.secret_1c = secret_1c

        self.additional_params = additional_params

    def create(self):
        """
        Формирует строку соединения с базой
        :return: str
        """
        str_infobase = self.infobase.get_parametrs()

        self.ConnectionString = f"{self.agent_type} {str_infobase}'/N '{self.username_1c}'/P '{self.secret_1c}"

        if self.agent_mode:
            self.ConnectionString += r'/AgentMode'
        if self.AgentSSHHostKeyAuto:
            self.ConnectionString += r'/AgentSSHHostKeyAuto'
        if self.AgentBaseDir:
            self.ConnectionString += self.AgentBaseDir

        for add_param in self.additional_params:
            if add_param in known_parametrs():
                self.ConnectionString += r'/' + self.AgentBaseDir

        return self.ConnectionString



