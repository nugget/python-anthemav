#!/usr/bin/env python3

import asynchat
import socket
import time
import logging

ATTRIBUTES = { 'Z1VOL', 'Z1POW', 'IDM', 'IDS', 'IDR', 'IDB', 'IDN', 'Z1VIR', 'Z1MUT', 'ICN'}

LOOKUP = {}

LOOKUP['Z1VIR'] = {'0': 'No Video', '1': 'Other Video', '2': '1080p60',
    '3': '1080p50', '4': '1080p24', '5': '1080i60', '6': '1080i50',
    '7': '720p60', '8': '720p50', '9': '576p50', '10': '576i50',
    '11': '480p60', '12': '480i60', '13': '3D', '14': '4K'}

class AnthemAVR(asynchat.async_chat):
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def doconnect(self, host, port=14999):
        self.logger.info('AnthemAV Attempting to connect')
        self.host = host
        self.port = port
        self.ibuffer = []
        self.obuffer = ""
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))
        self.set_terminator(b';')
        self.logger.info('AnthemAVR doconnect is done')

    def handle_connect(self):
        self.logger.debug('I am connected')
        self.populate()

    def handle_connect_event(self):
        self.logger.debug('I am connected by an event')
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            self.logger.warn('hrmity')
        self.connected = 1
        self.handle_connect()

    def handle_error(self):
        self.logger.warn('I had an error')
        time.sleep(10)

    def handle_excpt(self):
        self.logger.warn('I cannot spell exception')

    def populate(self):
        self._input_name = {}
        self._input_number = {}

        for key in ATTRIBUTES:
            setattr(self, '_'+key, "")
            self.query(key)

    def populate_inputs(self):
        top = int(self._ICN)+1
        for input_number in range(1,top):
            self.query('ISN'+str(input_number).zfill(2))

    def collect_incoming_data(self, data):
        self.ibuffer.append(data.decode('utf-8'))

    def found_terminator(self):
        for buf in self.ibuffer:
            self.parse(buf)
        self.ibuffer = []

    def command(self,code):
        b = bytearray()
        b.extend(map(ord,code+';'))
        self.push(b)

    def query(self,code):
        self.logger.debug('Querying '+code)
        self.command(code+'?')

    def parse(self, data):
        for key in ATTRIBUTES:
            if data.startswith(key):
                value = data[len(key):]
                self.logger.debug(key+' is a key for data '+data+' and value is '+value)
                setattr(self, '_'+key, value)

        if data.startswith('ICN'):
            self.logger.debug('Time to Pop')
            self.populate_inputs()

        if data.startswith('ISN'):
            input_number = int(data[3:5])
            value = data[5:]
            self.logger.debug('Input '+str(input_number)+' is '+value)
            self._input_number[value] = input_number
            self._input_name[input_number] = value
        return

    def turn_off(self):
        self.command('Z1POW0')

    def turn_on(self):
        self.command('Z1POW1;Z1POW')

    @property
    def power(self):
        try:
            return (self._Z1POW == 1)
        except:
            return False

    @property
    def muted(self):
        try:
            return (self._Z1MUT == 1)
        except:
            return False

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
    def rawvalue(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))
