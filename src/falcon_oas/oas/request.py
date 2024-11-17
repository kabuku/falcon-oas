import abc


from ..utils import cached_property


class Request(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def uri_template(self):
        # type: () -> str
        """Correspond to the key of Path Item Object."""

    @abc.abstractmethod
    def method(self):
        # type: () -> str
        """Correspond to the HTTP method of Operation Object."""

    @cached_property
    @abc.abstractmethod
    def parameters(self):
        # type: () -> Dict
        """The dict of request parameters like:

        {
            'query': {'page': '1'},
            'header': {'X-API-Key': 'secret'},
            'path': {'id': '42'},
            'cookie': {'session': 'secret'},
        }
        """

    @abc.abstractmethod
    def media_type(self):
        # type: () -> str
        """The media type of request without parameter."""

    @abc.abstractmethod
    def get_media(self):
        # type: () -> Any
        """The deserialized request body."""
