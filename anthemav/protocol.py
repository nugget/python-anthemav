import asyncio
import logging
from functools import partial

# In Python 3.4.4, `async` was renamed to `ensure_future`.
try:
    ensure_future = asyncio.ensure_future
except AttributeError:
    ensure_future = asyncio.async

ATTRIBUTES = { 'Z1VOL', 'Z1POW', 'IDM', 'IDS', 'IDR', 'IDB', 'IDH', 'IDN', 'Z1VIR', 'Z1MUT', 'ICN', 'Z1INP'}

class AnthemProtocol(asyncio.Protocol):
    def __init__(self, update_callback=None, loop=None, connection_lost_callback=None):
        self.loop = loop 
        self.log = logging.getLogger(__name__)
        self._connection_lost_callback = connection_lost_callback
        self._update_callback = update_callback
        self.buffer = ''
        self.retry = 10
        self._input_names = {}
        self._input_numbers = {}

        for key in ATTRIBUTES:
            setattr(self, '_'+key, "")

    def refresh_all(self):
        for key in ATTRIBUTES:
            self.query(key)

    def connection_made(self, transport):
        self.log.info('connection_made')
        self.transport = transport
        self.refresh_all()

    def data_received(self, data):
        self.buffer += data.decode()
        self.log.debug('Data received: {!r}'.format(data.decode()))
        self.assemble_buffer()

    def connection_lost(self, exc):
        if exc is None:
            self.log.warn('eof from receiver?')
        else:
            self.log.warn("Lost connection to %s" % exc)
            self._reader.set_exception(exc)

        self._is_connected = False
        self.transport = None

        if self._connection_lost_callback:
            self._connection_lost_callback()


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
                oldvalue = getattr(self, '_'+key)
                setattr(self, '_'+key, value)

                if key == 'Z1POW' and value == '1' and oldvalue != value:
                    self.refresh_all()

                break

        if data.startswith('ICN'):
            self.populate_inputs(int(value))

        if data.startswith('ISN'):
            input_number = int(data[3:5])
            value = data[5:]
            self._input_numbers[value] = input_number
            self._input_names[input_number] = value

        # I was using this for debugging/forensics
        # self.log.warn(self.dump_rawdata)
        
        if self._update_callback:
            self._update_callback(data)

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
            return round((value / 100) * 90) - 90
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
            self.log.debug('Setting attenuation to '+str(value))
            self.command('Z1VOL'+str(value))

    @property
    def volume(self):
        return self.attenuation_to_volume(self.attenuation)

    @volume.setter
    def volume(self, value):
        if isinstance(value, int) and 0 <= value <= 100:
            self.attenuation = self.volume_to_attenuation(value)

    @property
    def volume_as_percentage(self):
        vp = self.volume / 100
        return vp

    @volume_as_percentage.setter
    def volume_as_percentage(self,value):
        if isinstance(value, float) or isinstance(value, int):
            if 0 <= value <= 1:
                value = round(value * 100)
                self.volume = value

    @property
    def power(self):
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
    def input_list(self):
        return list(self._input_numbers.keys())

    @property
    def input_name(self):
        return self._input_names.get(self.input_number, "Unknown")

    @input_name.setter
    def input_name(self,value):
        number = self._input_numbers.get(value, 0)
        if number > 0:
            self.input_number = number

    @property
    def input_number(self):
        try:
            return int(self._Z1INP)
        except:
            return 0
    
    @input_number.setter
    def input_number(self,number):
        if isinstance(number, int):
            if 1 <= number <= 99:
                self.log.info('Switching input to '+str(number))
                self.command('Z1INP'+str(number))

    @property
    def staticstring(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))

    @property
    def dump_rawdata(self):
        attrs = vars(self)
        return(', '.join("%s: %s" % item for item in attrs.items()))
