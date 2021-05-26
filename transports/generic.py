import abc


class Transport(abc.ABC):
    """
    Abstract class for transport backends
    """

    def __init__(self, config):
        pass

    @abc.abstractmethod
    def send_message(self):
        pass
