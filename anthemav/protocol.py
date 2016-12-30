#!/usr/bin/env python3

import asyncio
import logging
from functools import partial

ATTRIBUTES = { 'Z1VOL', 'Z1POW', 'IDM', 'IDS', 'IDR', 'IDB', 'IDN', 'Z1VIR', 'Z1MUT', 'ICN'}

def create_anthemav_reader(host,port,message_callback,loop=None):
    protocol = partial(AnthemProtocol,host,port,message_callback,loop)
    conn = loop.create_connection(lambda: AnthemProtocol(host,port,message_callback,loop),host,port)
    return conn

class AnthemProtocol(asyncio.Protocol):
    def __init__(self, host, port, message_callback=None, loop=None):
        self._host = host
        self._port = port
        self.loop = loop 
        self.log = logging.getLogger(__name__)
        self.message_callback = message_callback
        self.buffer = ''

        for key in ATTRIBUTES:
            setattr(self, '_'+key, "")

    def connection_made(self, transport):
        self.log.info('connection_made')
        self.transport = transport

        message = 'Z1VOL?;'
        self.transport.write(message.encode())
        message = 'Z1POW?;'
        self.transport.write(message.encode())

    def data_received(self, data):
        self.buffer += data.decode()
        self.log.info('Data received: {!r}'.format(data.decode()))
        self.assemble_buffer()

    def connection_lost(self, exc):
        self.log.info('connection_lost')

    def assemble_buffer(self):
        self.transport.pause_reading()

        for command in self.buffer.split(';'):
            if command != '':
                self.log.info('command is '+command)
                self.parse_message(command)

        self.buffer = ""

        self.transport.resume_reading()
        return

    def parse_message(self,data):
        self.log.debug('parse '+data)
        for key in ATTRIBUTES:
            if data.startswith(key):
                value = data[len(key):]
                self.log.debug(key+' is a key for data '+data+' and value is '+value)
                setattr(self, '_'+key, value)

        self.log.warn(self.dump_rawdata)

        if self.message_callback:
            self.message_callback(self,data)

        return

    @property
    def attenuation(self):
        try:
            return int(self._Z1VOL)
        except:
            return -90

    @property
    def volume(self):
        try:
            return round((90.00 + int(self._Z1VOL)) / 90 * 100)
        except:
            return 0

    @property
    def volume_as_percentage(self):
        vp = self.volume / 100
        return vp

    @property
    def staticstring(self):
        return "I like cows"

    @property
    def dump_rawdata(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))
