from .protocol import AnthemProtocol
import asyncio
import logging

__all__ = ('Connection', )

try:
    ensure_future = asyncio.ensure_future
except:
    ensure_future = asyncio.async

class Connection:
    def __init__(self):
        self.log = logging.getLogger(__name__)

    @classmethod
    @asyncio.coroutine
    def create(cls, host='localhost', port=14999,
            auto_reconnect=True, loop=None, protocol_class=AnthemProtocol,
            update_callback=None):

        assert port >= 0, "Invalid port value: %r" % (port)
        conn = cls()

        conn.host = host
        conn.port = port
        conn._loop = loop or asyncio.get_event_loop()
        conn._retry_interval = 1
        conn._closed = False
        conn._closing = False
        conn._auto_reconnect = auto_reconnect

        def connection_lost():
            if conn._auto_reconnect and not conn._closing:
                ensure_future(conn._reconnect(), loop=conn._loop)

        conn.protocol = protocol_class(connection_lost_callback=connection_lost,
                loop=conn._loop, update_callback=update_callback)

        yield from conn._reconnect()

        return conn

    @property
    def transport(self):
        return self.protocol.transport

    def _get_retry_interval(self):
        return self._retry_interval

    def _reset_retry_interval(self):
        self._retry_interval = 1

    def _increase_retry_interval(self):
        self._retry_interval = min(300, 1.5 * self._retry_interval)

    @asyncio.coroutine
    def _reconnect(self):
        while True:
            try:
                self.log.info("Connecting to Anthem AVR at %s:%d" % (self.host, self.port))
                yield from self._loop.create_connection(lambda: self.protocol, self.host, self.port)
                self._reset_retry_interval()
                return
            except OSError:
                self._increase_retry_interval()
                interval = self._get_retry_interval()
                self.log.warn('Connecting failed, retrying in %i seconds' % interval)
                yield from asyncio.sleep(interval, loop=self._loop)

    def close(self):
        self._closing = True

        if self.protocol.transport:
            self.protocol.transport.close()

    @property
    def dump_conndata(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))
