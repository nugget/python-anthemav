import asyncio
import logging

# In Python 3.4.4, `async` was renamed to `ensure_future`.
try:
    ensure_future = asyncio.ensure_future
except AttributeError:
    ensure_future = asyncio.async

# These properties apply even when the AVR is powered off
ATTR_CORE = {'Z1POW', 'IDM'}

LOOKUP = {}

LOOKUP['Z1POW'] = {'description': 'Zone 1 Power',
        '0': 'Off', '1': 'On'}
LOOKUP['FPB'] = {'description': 'Front Panel Brightness', 
        '0': 'Off', '1': 'Low', '2': 'Medium', '3': 'High'}
LOOKUP['Z1VOL'] = {'description': 'Zone 1 Volume'}
LOOKUP['IDR'] = {'description': 'Region'}
LOOKUP['IDM'] = {'description': 'Model'}
LOOKUP['IDS'] = {'description': 'Software version'}
LOOKUP['IDB'] = {'description': 'Software build date'}
LOOKUP['IDH'] = {'description': 'Hardware version'}
LOOKUP['IDN'] = {'description': 'MAC address'}
LOOKUP['ECH'] = {'description': 'Tx status',
        '0': 'Off', '1': 'On'}
LOOKUP['SIP'] = {'description': 'Standby IP control',
        '0': 'Off', '1': 'On'}
LOOKUP['ICN'] = {'description': 'Active input count'}
LOOKUP['Z1INP'] = {'description': 'Zone 1 current input'}
LOOKUP['Z1MUT'] = {'description': 'Zone 1 mute',
        '0': 'Unmuted', '1': 'Muted'}
LOOKUP['Z1ARC'] = {'description': 'Zone 1 ARC',
        '0': 'Off', '1': 'On'}
LOOKUP['Z1VIR'] = {'description': 'Video input resolution',
        '0': 'No video', '1': 'Other', '2': '1080p60', '3': '1080p50',
        '4': '1080p24', '5': '1080i60', '6': '1080i50', '7': '720p60',
        '8': '720p50', '9': '576p50', '10': '576i50', '11': '480p60',
        '12': '480i60', '13': '3D', '14': '4K'}
LOOKUP['Z1IRH'] = {'description': 'Active horizontal video resolution (pixels)'}
LOOKUP['Z1IRV'] = {'description': 'Active vertical video resolution (pixels)'}
LOOKUP['Z1AIC'] = {'description': 'Audio input channels',
        '0': 'No audio', '1': 'Other', '2': 'Mono (center channel only)',
        '3': '2 channel', '4': '5.1 channel', '5': '6.1 channel',
        '6': '7.1 channel', '7': 'Atmos'}
LOOKUP['Z1AIF'] = {'description': 'Audio input format',
        '0': 'No audio', '1': 'Analog', '2': 'PCM', '3': 'Dolby', '4': 'DSD',
        '5': 'DTS', '6': 'Atmos'}
LOOKUP['Z1BRT'] = {'description': 'Audio input bitrate (kbps)'}
LOOKUP['Z1SRT'] = {'description': 'Audio input sampling rate (hKz)'}
LOOKUP['Z1AIN'] = {'description': 'Audio input name'}
LOOKUP['Z1AIR'] = {'description': 'Audio input rate name'}
LOOKUP['Z1ALM'] = {'description': 'Audio listening mode',
        '00': 'None', '01': 'AnthemLogic Movie', '02': 'AnthemLogic Music',
        '03': 'PLIIx Movie', '04': 'PLIIx Music', '05': 'Neo:6 Cinema',
        '06': 'Neo:6 Music', '07': 'All Channel Stereo',
        '08': 'All Channel Mono', '09': 'Mono', '10': 'Mono-Academy',
        '11': 'Mono (L)', '12': 'Mono (R)', '13': 'High Blend',
        '14': 'Dolby Surround', '15': 'Neo:X Cinema', '16': 'Neo:X Music'}
LOOKUP['Z1DYN'] = {'description': 'Dolby digital dynamic range',
        '0': 'Normal', '1': 'Reduced', '2': 'Late Night'}
LOOKUP['Z1DIA'] = {'description': 'Dolby digital dialog normalization (dB)'}

class AnthemProtocol(asyncio.Protocol):
    """The Athem AVR IP control protocol handler

    This is the protocol handler that handles all status updates and command
    issuances to the device.  It is expected to be wrapped inside a Connection
    class object which will maintain the socket and handle auto-reconnects.

        :param update_callback: (optional) called if any state information changes in device
        :param connection_lost_callback: (optional) called when connection is lost to device
        :param loop: (optional) asyncio event loop
    """
    def __init__(self, update_callback=None, loop=None, connection_lost_callback=None):
        self._loop = loop 
        self.log = logging.getLogger(__name__)
        self._connection_lost_callback = connection_lost_callback
        self._update_callback = update_callback
        self.buffer = ''
        self._input_names = {}
        self._input_numbers = {}

        for key in LOOKUP.keys():
            setattr(self, '_'+key, "")

        self._Z1POW = '0'

    def refresh_core(self):
        """Query device for all attributes that exist regardless of power state

        This will force a refresh for all device queries that are valid to
        request at any time.  It's the only safe suite of queries that we can 
        make if we do not know the current state (on or off+standby).

        This does not return any data, it just issues the queries.
        """
        self.log.info('refresh_core')
        for key in ATTR_CORE:
            self.query(key)


    def refresh_all(self):
        """Query device for all attributes that are known

        This will force a refresh for all device queries that the module is 
        aware of.  In theory, this will completely populate the internal state
        table for all attributes.

        This does not return any data, it just issues the queries.
        """
        for key in LOOKUP.keys():
            self.query(key)

    #
    # asyncio network functions
    #

    def connection_made(self, transport):
        self.log.info('Connection established to AVR')
        self.transport = transport

        self.transport.set_write_buffer_limits(128)
        limit_low,limit_high = self.transport.get_write_buffer_limits()
        self.log.debug("Write buffer limits %d to %d" % (limit_low, limit_high))

        self.refresh_core()

    def data_received(self, data):
        self.buffer += data.decode()
        self.log.debug('Data received: {!r}'.format(data.decode()))
        self._assemble_buffer()

    def connection_lost(self, exc):
        if exc is None:
            self.log.warn('eof from receiver?')
        else:
            self.log.warn("Lost connection to receiver: %s" % exc)

        self._is_connected = False
        self.transport = None

        if self._connection_lost_callback:
            self._connection_lost_callback()


    def _assemble_buffer(self):
        """Split up received data from device into individual commands

        Data sent by the device is a sequence of datagrams separated by 
        semicolons.  It's common to receive a burst of them all in one
        submission when there's a lot of device activity.  This function
        disassembles the chain of datagrams into individual messages which
        are then passed on for interpretation.
        """
        self.transport.pause_reading()

        for message in self.buffer.split(';'):
            if message != '':
                self.log.debug('assembled message '+message)
                self._parse_message(message)

        self.buffer = ""

        self.transport.resume_reading()
        return

    def _populate_inputs(self,total):
        """Request the names for all active, configured inputs on the device

        Once we learn how many inputs are configured, this function is called
        which will ask for the name of each active input.
        """
        total = total + 1
        for input_number in range(1,total):
            self.query('ISN'+str(input_number).zfill(2))

    def _parse_message(self,data):
        """Interpret each message datagram from device and do the needful

        This function receives datagrams from _assemble_buffer and inerprets 
        what they mean.  It's responsible for maintaining the internal state
        table for each device attribute and also for firing the update_callback
        function (if one was supplied)
        """
        recognized = False
        newdata = False

        if data.startswith('!I'):
            self.log.warn("Invalid command: %s" % data[2:])
            recognized = True
        elif data.startswith('!R'):
            self.log.warn("Out-of-range command: %s" % data[2:])
            recognized = True
        elif data.startswith('!E'):
            self.log.warn("Cannot execute recognized command: %s" % data[2:])
            recognized = True
        elif data.startswith('!Z'):
            self.log.warn("Ignoring command for powered-off zone: %s" % data[2:])
            recognized = True
        else:

            for key in LOOKUP.keys():
                if data.startswith(key):
                    recognized = True

                    value = data[len(key):]
                    oldvalue = getattr(self, '_'+key)
                    if oldvalue != value:
                        changeindicator = 'New Value'
                        newdata = True
                    else:
                        changeindicator = 'Unchanged'


                    if key in LOOKUP:
                        if 'description' in LOOKUP[key]:
                            if value in LOOKUP[key]:
                                self.log.info("%s: %s (%s) -> %s (%s)" % (changeindicator,LOOKUP[key]['description'], key, LOOKUP[key][value], value))
                            else:
                                self.log.info("%s: %s (%s) -> %s" % (changeindicator,LOOKUP[key]['description'], key, value))
                    else:
                        self.log.info("%s: %s -> %s" % (changeindicator,key, value))

                    setattr(self, '_'+key, value)

                    if key == 'Z1POW' and value == '1' and oldvalue == '0':
                        self.log.info('Power on detected, refreshing all attributes')
                        self.refresh_all()

                    break

        if data.startswith('ICN'):
            recognized = True
            self._populate_inputs(int(value))

        if data.startswith('ISN'):
            recognized = True

            input_number = int(data[3:5])
            value = data[5:]

            oldname = self._input_names.get(input_number, '')

            if oldname != value:
                self._input_numbers[value] = input_number
                self._input_names[input_number] = value
                self.log.info("New Value: Input %d is called %s" % (input_number, value))
                newdata = True

        if newdata:
            if self._update_callback:
                self._update_callback(data)

        if not recognized:
            self.log.warn("Unrecognized response: %s" % data)

    def query(self,item):
        """Issue a raw query to the device for an item

        This function is used to request that the device supply the current
        state for a data item as described in the Anthem IP protocoal API.
        Normal interaction with this module will not require you to make raw
        device queries with this function, but the method is exposed in case
        there's a need that's not otherwise met by the abstraction methods
        defined elsewhere.

        This function does not return the result, it merely issues the request.

            :param item: Any of the data items from the API
            :type item: str

        :Example:

        >>> query('Z1VOL')

        """
        item = item+'?'
        self.command(item)

    def command(self,command):
        """Issue a raw command to the device 

        This function is used to update a data item on the device.  It's used
        to cause activity or change the configuration of the AVR.  Normal
        interaction with this module will not require you to make raw device
        queries with this function, but the method is exposed in case there's a
        need that's not otherwise met by the abstraction methods defined
        elsewhere.

            :param command: Any command as documented in the Anthem API
            :type command: str

        :Example:

        >>> command('Z1VOL-50')
        """
        command = command+';'
        self.formatted_command(command)

    def formatted_command(self,command):
        """Issue a raw, formatted command to the device 

        This function is invoked by both query and command and is the point
        where we actually send bytes out over the network.  This function does
        the wrapping and formatting required by the Anthem API so that the
        higher-level function can just operate with regular strings without 
        the burden of byte encoding and terminating device requests.

            :param command: Any command as documented in the Anthem API
            :type command: str

        :Example:

        >>> formatted_command('Z1VOL-50')
        """
        command = command
        command = command.encode()

        if hasattr(self, 'transport'):
            self.log.debug("> %s" % command)
            self.transport.write(command)
        else:
            self.log.warn('No transport found, unable to send command')

    # 
    # Volume and Attenuation handlers.  The Anthem tracks volume internally as
    # an attenuation level ranging from -90dB (silent) to 0dB (bleeding ears)
    #
    # We expose this in three methods for the convenience of downstream apps
    # which will almost certainly be doing things their own way:
    #
    #   - attenuation (-90 to 0)
    #   - volume (0-100)
    #   - volume_as_percentage (0-1 floating point)
    #

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


    #
    # Internal assistant functions for unified handling of boolean 
    # properties that are read/write
    #
    
    def _get_boolean(self,key):
        keyname = '_'+key
        value = '0'
        if hasattr(self, keyname):
            value = getattr(self, keyname)

        if value == '1':
            return True
        else:
            return False

    def _set_boolean(self,key,value):
        if value == True:
            self.command(key+'1')
        else:
            self.command(key+'0')

    #
    # Boolean properties and corresponding setters
    #

    @property
    def power(self):
        return self._get_boolean('Z1POW')

    @power.setter
    def power(self,value):
        self._set_boolean('Z1POW',value)


    @property
    def txstatus(self):
        return self._get_boolean('ECH')

    @txstatus.setter
    def txstatus(self,value):
        self._set_boolean('ECH',value)


    @property
    def standby_control(self):
        return self._get_boolean('SIP')
    
    @standby_control.setter
    def standby_control(self,value):
        self._set_boolean('SIP',value)


    @property
    def arc(self):
        return self._get_boolean('Z1ARC')

    @arc.setter
    def arc(self,value):
        self._set_boolean('Z1ARC',value)

    
    @property
    def mute(self):
        self._get_boolean('Z1MUT')

    @mute.setter
    def mute(self,value):
        self._set_boolean('Z1MUT',value)



    #
    # Read-only text properties
    #

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
    def audio_input_name(self):
        return self._Z1AIN or "Unknown"

    @property
    def audio_input_ratename(self):
        return self._Z1AIR or "Unknown"


    #
    # Read-only raw numeric properties
    #
   
    def _get_integer(self,key):
        keyname = '_'+key
        if hasattr(self, keyname):
            value = getattr(self, keyname)
        try:
            return int(value)
        except:
            return 

    @property
    def dolby_dialog_normalization(self):
        return self._get_integer('Z1DIA')

    @property
    def horizontal_resolution(self):
        return self._get_integer('Z1IRH')

    @property
    def vertical_resolution(self):
        return self._get_integer('Z1IRV')

    @property
    def audio_input_bitrate(self):
        return self._get_integer('Z1BRT')

    @property
    def audio_input_samplerate(self):
        return self._get_integer('Z1SRT')


    #
    # Helper functions for working with raw/text multi-property items
    #
    #
    def _get_multiprop(self, key, mode='raw'):
        keyname = '_'+key

        if hasattr(self, keyname):
            rawvalue = getattr(self, keyname)
            value = rawvalue

            if key in LOOKUP:
                if rawvalue in LOOKUP[key]:
                    value = LOOKUP[key][rawvalue]

            if mode == 'raw':
                return rawvalue
            else:
                return value
        else:
            return

    #
    # Read/write properties with raw and text options
    #
    #
    @property
    def panel_brightness(self):
        return self._get_multiprop('FPB', mode='raw')

    @property
    def panel_brightness_text(self):
        return self._get_multiprop('FPB', mode='text')

    @panel_brightness.setter
    def panel_brightness(self,number):
        if isinstance(number, int):
            if 0 <= number <= 3:
                self.log.info('Switching panel brightness to '+str(number))
                self.command('FPB'+str(number))


    @property
    def audio_listening_mode(self):
        return self._get_multiprop('Z1ALM', mode='raw')

    @property
    def audio_listening_mode_text(self):
        return self._get_multiprop('Z1ALM', mode='text')

    @audio_listening_mode.setter
    def audio_listening_mode(self,number):
        if isinstance(number, int):
            if 0 <= number <= 16:
                self.log.info('Switching audio listening mode to '+str(number))
                self.command('Z1ALM'+str(number).zfill(2))


    @property
    def dolby_dynamic_range(self):
        return self._get_multiprop('Z1DYN', mode='raw')

    @property
    def dolby_dynamic_range_text(self):
        return self._get_multiprop('Z1DYN', mode='text')

    @dolby_dynamic_range.setter
    def dolby_dynamic_range(self,number):
        if isinstance(number, int):
            if 0 <= number <= 2:
                self.log.info('Switching Dolby dynamic range to '+str(number))
                self.command('Z1DYN'+str(number))


    #
    # Read-only properties with raw and text options
    #

    @property
    def video_input_resolution(self):
        return self._get_multiprop('Z1VIR', mode='raw')

    @property
    def video_input_resolution_text(self):
        return self._get_multiprop('Z1VIR', mode='text')

    @property
    def audio_input_channels(self):
        return self._get_multiprop('Z1AIC', mode='raw')

    @property
    def audio_input_channels_text(self):
        return self._get_multiprop('Z1AIC', mode='text')

    @property
    def audio_input_format(self):
        return self._get_multiprop('Z1AIF', mode='raw')

    @property
    def audio_input_format_text(self):
        return self._get_multiprop('Z1AIF', mode='text')


    #
    # Input number and lists
    #
 
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
        return self._get_integer('Z1INP')
    
    @input_number.setter
    def input_number(self,number):
        if isinstance(number, int):
            if 1 <= number <= 99:
                self.log.info('Switching input to '+str(number))
                self.command('Z1INP'+str(number))

    #
    # Miscellany 
    #

    @property
    def dump_rawdata(self):
        if hasattr(self, 'transport'):
            attrs = vars(self.transport)
            return(', '.join("%s: %s" % item for item in attrs.items()))

    @property
    def test_string(self):
        return "I like cows"
