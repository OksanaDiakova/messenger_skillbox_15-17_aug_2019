#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None

    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики

        self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике

        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера

    def send_history(self):
        """
        Высылает клиенту историю чата

        не более 10 последних сообщений
        """

        if len(self.factory.history) < 10:  # узнаем количество сообщений в истории
            self.sendLine(f"The latest {len(self.factory.history)} messages:".encode())
            for msg in self.factory.history:
                self.sendLine(msg.encode())
        else:
            self.sendLine("The latest 10 messages:".encode())
            for msg in self.factory.history[-10:]:
                self.sendLine(msg.encode())

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку

        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:
                self.login = message.replace("login:", "")  # вырезаем часть после :
                if self.login in self.factory.lst_of_log:
                    # посылаем уведомление, что логин занят
                    self.sendLine(f"Login {self.login} is not available. Please, choose another one.".encode())
                    # отключаем клиента
                    self.transport.loseConnection()
                else:
                    notification = f"New user: {self.login}"  # формируем уведомление о новом клиенте
                    self.factory.lst_of_log.append(self.login)  # добавляем логин в список логинов
                    self.factory.history.append(notification)  # добавляем сообщение в историю чата
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат
                    self.send_history()  # посылаем клиенту последние сообщения из чата
            else:
                self.sendLine("Invalid login".encode())  # шлем уведомление, если в сообщении ошибка
        # если логин уже есть и это следующее сообщение
        else:
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента
            self.factory.history.append(format_message)
            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    lst_of_log: list  # список логинов
    history: list  # история чата
    protocol = Client  # протокол обработки клиента

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов
        self.lst_of_log = []  # список логинов
        self.history = []  # история чата

        print("Server started - OK")  # уведомление в консоль сервера

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")  # уведомление в консоль сервера

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        data = message.encode()  # закодируем текст в двоичное представление

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
