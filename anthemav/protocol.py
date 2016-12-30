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
        self.retry = 10
        self._input_name = {}
        self._input_number = {}

        for key in ATTRIBUTES:
            setattr(self, '_'+key, "")

    def connection_made(self, transport):
        self.log.info('connection_made')
        self.transport = transport

        for key in ATTRIBUTES:
            self.query(key)

    def data_received(self, data):
        self.buffer += data.decode()
        self.log.debug('Data received: {!r}'.format(data.decode()))
        self.assemble_buffer()

    def connection_lost(self, exc):
        self.log.info('connection_lost')


    def assemble_buffer(self):
        self.transport.pause_reading()

        for message in self.buffer.split(';'):
            if message != '':
                self.log.debug('assembled message '+message)
                self.parse_message(message)

        self.buffer = ""

        self.transport.resume_reading()
        return

    def populate_inputs(self,total):
        total = total + 1
        for input_number in range(1,total):
            self.query('ISN'+str(input_number).zfill(2))

    def parse_message(self,data):
        for key in ATTRIBUTES:
            if data.startswith(key):
                value = data[len(key):]
                self.log.info('Received value for '+key+': '+value)
                setattr(self, '_'+key, value)

        if data.startswith('ICN'):
            self.populate_inputs(int(value))

        if data.startswith('ISN'):
            input_number = int(data[3:5])
            value = data[5:]
            self.log.debug('Input '+str(input_number)+' is '+value)
            self._input_number[value] = input_number
            self._input_name[input_number] = value

        # I was using this for debugging/forensics
        # self.log.warn(self.dump_rawdata)
        
        if self.message_callback:
            self.message_callback(self,data)

        return

    def ping(self):
        self.log.info('Request to Ping')
        message = 'Z1POW?;'
        self.transport.write(message.encode())


    def query(self,message):
        message = message+'?'
        self.command(message)

    def command(self,message):
        message = message+';'
        self.raw_command(message)

    def raw_command(self,message):
        message = message.encode()

        if hasattr(self, 'transport'):
            self.transport.write(message)
        else:
            self.log.warn('No transport found, unable to send command')

    def attenuation_to_volume(self,value):
        try:
            return round((90.00 + int(value)) / 90 * 100) 
        except:
            return 0

    def volume_to_attenuation(self,value):
        try:
            return rount((value / 100) * -90)
        except:
            return -90

    @property
    def attenuation(self):
        try:
            return int(self._Z1VOL) 
        except:
            return -90

    @attenuation.setter
    def attenuation(self,value):
        if isinstance(value, int) and -90 <= value <= 0:
            self.command('Z1VOL'+str(value))

    @property
    def volume(self):
        return self.attenuation_to_volume(self.attenuation)

    @volume.setter
    def volume(self, value):
        if isinstance(value, int) and 0 <= value <= 100:
            self.command('Z1VOL'+str(self.volume_to_attenuation(value)))

    @property
    def volume_as_percentage(self):
        vp = self.volume / 100
        return vp

    @volume_as_percentage.setter
    def volume_as_percentage(self,value):
        if isinstance(value, float) or isinstance(value, int):
            if 0 <= value <= 1:
                value = value * 100
                self.volume = value

    @property
    def power(self):
        self.log.debug('request for power '+self._Z1POW)
        if self._Z1POW == '1':
            return True
        elif self._Z1POW == '0':
            return False
        else:
            return
    @power.setter
    def power(self,value):
        if value == True:
            self.command('Z1POW1')
        else:
            self.command('Z1POW0')

    @property
    def model(self):
        return self._IDM or "Unknown Model"

    @property
    def swversion(self):
        return self._IDS or "Unknown Version"

    @property
    def region(self):
        return self._IDR or "Unknown Region"

    @property
    def build_date(self):
        return self._IDB or "Unknown Build Date"

    @property
    def hwversion(self):
        return self._IDH or "Unknown Version"

    @property
    def macaddress(self):
        return self._IDN or "00:00:00:00:00:00"

    @property
    def staticstring(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))

    @property
    def dump_rawdata(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))
