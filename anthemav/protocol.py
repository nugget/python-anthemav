"""Module to maintain AVR state information and network interface."""
import asyncio
import logging
from typing import Awaitable, Callable

__all__ = ["AVR"]

# These properties apply even when the AVR is powered off
ATTR_CORE = {"Z1POW", "IDM"}

# Audio Listening mode
ALM_NUMBER = {
    "None": 0,
    "AnthemLogic Cinema": 1,
    "AnthemLogic Music": 2,
    "PLII Movie": 3,
    "PLII Music": 4,
    "Neo Cinema": 5,
    "Neo Music": 6,
    "All Channel": 7,
    "All Channel Mono": 8,
    "Mono": 9,
    "Mono-Academy": 10,
    "Mono (L)": 11,
    "Mono (R)": 12,
    "High Blend": 13,
    "Dolby Surround": 14,
}

# Some models (eg:MRX 520) provide a limited list of listening mode
ALM_RESTRICTED = ["00", "01", "02", "03", "04", "05", "06", "07"]

ALM_RESTRICTED_MODEL = ["MRX 520"]

LOOKUP = {}

LOOKUP["Z1POW"] = {"description": "Zone 1 Power", "0": "Off", "1": "On"}
LOOKUP["Z1VOL"] = {"description": "Zone 1 Volume"}
LOOKUP["IDR"] = {"description": "Region"}
LOOKUP["IDM"] = {"description": "Model"}
LOOKUP["IDS"] = {"description": "Software version"}
LOOKUP["IDB"] = {"description": "Software build date"}
LOOKUP["IDH"] = {"description": "Hardware version"}
LOOKUP["ICN"] = {"description": "Active input count"}
LOOKUP["Z1INP"] = {"description": "Zone 1 current input"}
LOOKUP["Z1MUT"] = {"description": "Zone 1 mute", "0": "Unmuted", "1": "Muted"}
LOOKUP["Z1VIR"] = {
    "description": "Video input resolution",
    "0": "No video",
    "1": "Other",
    "2": "1080p60",
    "3": "1080p50",
    "4": "1080p24",
    "5": "1080i60",
    "6": "1080i50",
    "7": "720p60",
    "8": "720p50",
    "9": "576p50",
    "10": "576i50",
    "11": "480p60",
    "12": "480i60",
    "13": "3D",
    "14": "4K",
}
LOOKUP["Z1IRH"] = {"description": "Active horizontal video resolution (pixels)"}
LOOKUP["Z1IRV"] = {"description": "Active vertical video resolution (pixels)"}
LOOKUP["Z1AIC"] = {
    "description": "Audio input channels",
    "0": "No audio",
    "1": "Other",
    "2": "Mono (center channel)",
    "3": "2 channel",
    "4": "5.1 channel",
    "5": "6.1 channel",
    "6": "7.1 channel",
    "7": "Atmos",
}
LOOKUP["Z1AIF"] = {
    "description": "Audio input format",
    "0": "No audio",
    "1": "Analog",
    "2": "PCM",
    "3": "Dolby",
    "4": "DSD",
    "5": "DTS",
    "6": "Atmos",
}
LOOKUP["Z1BRT"] = {"description": "Audio input bitrate (kbps)"}
LOOKUP["Z1SRT"] = {"description": "Audio input sampling rate (hKz)"}
LOOKUP["Z1AIN"] = {"description": "Audio input name"}
LOOKUP["Z1AIR"] = {"description": "Audio input rate name"}
LOOKUP["Z1ALM"] = {
    "description": "Audio listening mode",
    "00": "None",
    "01": "AnthemLogic Cinema",
    "02": "AnthemLogic Music",
    "03": "PLII Movie",
    "04": "PLII Music",
    "05": "Neo Cinema",
    "06": "Neo Music",
    "07": "All Channel",
    "08": "All Channel Mono",
    "09": "Mono",
    "10": "Mono-Academy",
    "11": "Mono (L)",
    "12": "Mono (R)",
    "13": "High Blend",
    "14": "Dolby Surround",
    "15": "Neo Cinema",
    "16": "Neo Music",
}
LOOKUP["Z1DYN"] = {
    "description": "Dolby digital dynamic range",
    "0": "Normal",
    "1": "Reduced",
    "2": "Late Night",
}
LOOKUP["Z1DIA"] = {"description": "Dolby digital dialog normalization (dB)"}

# Model specific lookupp
# MRX 520, 720, 1120
LOOKUP["IDN"] = {"description": "MAC address"}
LOOKUP["ECH"] = {"description": "Tx status", "0": "Off", "1": "On"}
LOOKUP["SIP"] = {"description": "Standby IP control", "0": "Off", "1": "On"}
LOOKUP["Z1ARC"] = {"description": "Zone 1 ARC", "0": "Off", "1": "On"}
LOOKUP["FPB"] = {
    "description": "Front Panel Brightness",
    "0": "Off",
    "1": "Low",
    "2": "Medium",
    "3": "High",
}

# MRX 540, 740, 1140
LOOKUP["WMAC"] = {"description": "Wi-Fi MAC address"}
LOOKUP["EMAC"] = {"description": "Ethernet MAC address"}
LOOKUP["IS1ARC"] = {"description": "Zone 1 ARC", "0": "Off", "1": "On"}
LOOKUP["GCFPB"] = {"description": "Front Panel Brightness"}
LOOKUP["GCTXS"] = {
    "description": "Tx status",
    "0": "Off",
    "1": "IP On",
    "2": "IP and RS232 on",
}

COMMANDS_X20 = ["IDN", "ECH", "SIP", "Z1ARC", "FPB"]
COMMANDS_X40 = ["WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS"]

EMPTY_MAC = "00:00:00:00:00:00"


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class AVR(asyncio.Protocol):
    """The Anthem AVR IP control protocol handler."""

    def __init__(
        self,
        update_callback: Callable[[str], None] = None,
        loop: asyncio.AbstractEventLoop = None,
        connection_lost_callback: Callable[[], Awaitable[None]] = None,
    ):
        """Protocol handler that handles all status and changes on AVR.

        This class is expected to be wrapped inside a Connection class object
        which will maintain the socket and handle auto-reconnects.

            :param update_callback:
                called if any state information changes in device (optional)
            :param connection_lost_callback:
                called when connection is lost to device (optional)
            :param loop:
                asyncio event loop (optional)

            :type update_callback:
                callable
            :type: connection_lost_callback:
                callable
            :type loop:
                asyncio.loop
        """
        self._loop = loop
        self.log = logging.getLogger(__name__)
        self._connection_lost_callback = connection_lost_callback
        self._update_callback = update_callback
        self.buffer = ""
        self._input_names = {}
        self._input_numbers = {}
        self._poweron_refresh_successful = False
        self.transport: asyncio.Transport = None
        self._ignored_commands = []
        self._force_refresh = False
        self._model_series = ""
        self._deviceinfo_received = asyncio.Event()

        for key in LOOKUP:
            setattr(self, f"_{key}", "")

        self._Z1POW = "0"

    async def wait_for_device_initialised(self, timeout: float):
        """Wait to receive the model and mac address for the device"""
        await asyncio.wait_for(self._deviceinfo_received.wait(), timeout)
        self.log.debug("device is initialised")

    def _set_device_initialised(self):
        """Indicate if the model and mac address have been received"""
        if self._model_series and self.macaddress != EMPTY_MAC:
            self._deviceinfo_received.set()

    async def refresh_core(self):
        """Query device for all attributes that exist regardless of power state.

        This will force a refresh for all device queries that are valid to
        request at any time.  It's the only safe suite of queries that we can
        make if we do not know the current state (on or off+standby).

        This does not return any data, it just issues the queries.
        """
        self.log.debug("Sending out mass query for all attributes")
        for key in ATTR_CORE:
            if self.transport is None:
                self.log.warning("Lost connection to receiver while refreshing device")
                break
            self.query(key)
            # small delay between command
            await asyncio.sleep(0.01)

    async def poweron_refresh(self):
        """Keep requesting all attributes until it works.

        Immediately after a power on event (POW1) the AVR is inconsistent with
        which attributes can be successfully queried.  When we detect that
        power has just been turned on, we loop every second making a bulk
        query for every known attribute.  This continues until we detect that
        values have been returned for at least one input name (this seems to
        be the laggiest of all the attributes)
        """
        if self._poweron_refresh_successful or self.transport is None:
            return
        else:
            await self.refresh_all()
            await asyncio.sleep(2)
            await self.poweron_refresh()

    async def refresh_all(self):
        """Query device for all attributes that are known.

        This will force a refresh for all device queries that the module is
        aware of.  In theory, this will completely populate the internal state
        table for all attributes.

        This does not return any data, it just issues the queries.
        """
        self.log.debug("refresh_all")
        for key in {k: v for k, v in LOOKUP.items() if k not in self._ignored_commands}:
            if self.transport is None:
                self.log.warning("Lost connection to receiver while refreshing device")
                break
            self.query(key)
            # small delay between command
            await asyncio.sleep(0.01)

    #
    # asyncio network functions
    #

    def connection_made(self, transport: asyncio.Transport):
        """Called when asyncio.Protocol establishes the network connection."""
        self.log.debug("Connection established to AVR")
        self.transport = transport

        # self.transport.set_write_buffer_limits(0)
        limit_low, limit_high = self.transport.get_write_buffer_limits()
        self.log.debug("Write buffer limits %d to %d", limit_low, limit_high)

        asyncio.run_coroutine_threadsafe(self.refresh_core(), self._loop)

    def data_received(self, data):
        """Called when asyncio.Protocol detects received data from network."""
        self.buffer += data.decode()
        self.log.debug("Received %d bytes from AVR: %s", len(self.buffer), self.buffer)
        self._assemble_buffer()

    def connection_lost(self, exc):
        """Called when asyncio.Protocol loses the network connection."""
        self.log.warning("Lost connection to receiver")

        if exc is not None:
            self.log.debug(exc)

        self.transport = None

        if self._connection_lost_callback:
            asyncio.run_coroutine_threadsafe(
                self._connection_lost_callback(), self._loop
            )

    def _assemble_buffer(self):
        """Split up received data from device into individual commands.

        Data sent by the device is a sequence of datagrams separated by
        semicolons.  It's common to receive a burst of them all in one
        submission when there's a lot of device activity.  This function
        disassembles the chain of datagrams into individual messages which
        are then passed on for interpretation.
        """
        self.transport.pause_reading()

        for message in self.buffer.split(";"):
            if message != "":
                self.log.debug("assembled message %s", message)
                self._parse_message(message)

        self.buffer = ""

        self.transport.resume_reading()
        return

    def _populate_inputs(self, total):
        """Request the names for all active, configured inputs on the device.

        Once we learn how many inputs are configured, this function is called
        which will ask for the name of each active input.
        """
        total = total + 1
        for input_number in range(1, total):
            if self._model_series == "x40":
                self.query(f"IS{input_number}IN")
            else:
                self.query(f"ISN{input_number:02d}")

    def _parse_message(self, data: str):
        """Interpret each message datagram from device and do the needful.

        This function receives datagrams from _assemble_buffer and inerprets
        what they mean.  It's responsible for maintaining the internal state
        table for each device attribute and also for firing the update_callback
        function (if one was supplied)
        """
        recognized = False
        newdata = False

        if data.startswith("!I"):
            self.log.warning("Invalid command: %s", data[2:])
            recognized = True
        elif data.startswith("!R"):
            self.log.warning("Out-of-range command: %s", data[2:])
            recognized = True
        elif data.startswith("!E"):
            self.log.debug("Cannot execute recognized command: %s", data[2:])
            recognized = True
        elif data.startswith("!Z"):
            self.log.debug("Ignoring command for powered-off zone: %s", data[2:])
            recognized = True
        else:

            for key, commands in LOOKUP.items():
                if data.startswith(key):
                    recognized = True

                    value = data[len(key) :]
                    oldvalue = getattr(self, "_" + key)
                    if oldvalue != value:
                        changeindicator = "New Value"
                        newdata = True
                    else:
                        changeindicator = "Unchanged"

                    if "description" in commands:
                        if value in commands:
                            self.log.debug(
                                "%s: %s (%s) -> %s (%s)",
                                changeindicator,
                                commands["description"],
                                key,
                                commands[value],
                                value,
                            )
                        else:
                            self.log.debug(
                                "%s: %s (%s) -> %s",
                                changeindicator,
                                commands["description"],
                                key,
                                value,
                            )

                    setattr(self, "_" + key, value)

                    if key == "IDM" and value != oldvalue:
                        self.set_model_command(value)

                    if key == "IDM" or key == "IDN" or key == "EMAC" or key == "WMAC":
                        self._set_device_initialised()

                    if key == "Z1POW" and value == "1" and oldvalue == "0":
                        self.log.debug("Power on detected, refreshing all attributes")
                        self._poweron_refresh_successful = False
                        self._loop.call_later(
                            1,
                            asyncio.run_coroutine_threadsafe,
                            self.poweron_refresh(),
                            self._loop,
                        )

                    if key == "Z1POW" and value == "0" and oldvalue == "1":
                        self._poweron_refresh_successful = False

                    if (
                        self._force_refresh is False
                        and self._Z1POW == "0"
                        and all(coreKey not in key for coreKey in ATTR_CORE)
                    ):
                        # AVR doesn't send Power State ON
                        # force refresh power state when receiving any command from a potential powered on AVR
                        self._force_refresh = True
                        self.log.debug("Force refresh Power State")
                        self.query("Z1POW")
                        self._loop.call_later(2, setattr, self, "_force_refresh", False)

                    break

        if data.startswith("ICN"):
            self.log.debug("ICN update received")
            self._poweron_refresh_successful = True
            recognized = True
            self._populate_inputs(int(value))

        if data.startswith("ISN"):  # x20 series: ISN01Turntable
            recognized = True
            self._poweron_refresh_successful = True

            input_number = int(data[3:5])
            value = data[5:]

            oldname = self._input_names.get(input_number, "")

            if oldname != value:
                self._input_numbers[value] = input_number
                self._input_names[input_number] = value
                self.log.debug("New Value: Input %d is called %s", input_number, value)
                newdata = True
        elif data.startswith("IS"):  # x40 series, example "IS3INTurntable"
            recognized = True
            self._poweron_refresh_successful = True
            in_position = data.index("IN")
            input_number = int(data[2:in_position])
            value = data[in_position + 2 :]
            oldname = self._input_names.get(input_number, "")

            if oldname != value:
                self._input_numbers[value] = input_number
                self._input_names[input_number] = value
                self.log.debug("New Value: Input %d is called %s", input_number, value)
                newdata = True

        if newdata:
            if self._update_callback:
                self._loop.call_soon(self._update_callback, data)
        else:
            self.log.debug("no new data encountered")

        if not recognized:
            self.log.debug("Unrecognized response: %s", data)

    def query(self, item: str):
        """Issue a raw query to the device for an item.

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
        item = item + "?"
        self.command(item)

    def set_model_command(self, model: str):
        """Add the commands to the model."""
        if "40" in model or "70" in model or "90" in model:
            self.log.debug("Set Command to Model x40")
            self._ignored_commands = COMMANDS_X20
            self._model_series = "x40"
            self.query("EMAC")
            self.query("WMAC")
        else:
            self.log.debug("Set Command to Model x20")
            self._ignored_commands = COMMANDS_X40
            self._model_series = "x20"
            self.command("ECH1")
            self.query("IDN")

    def command(self, command: str):
        """Issue a raw command to the device.

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
        command = command + ";"
        self.formatted_command(command)

    def formatted_command(self, command: str):
        """Issue a raw, formatted command to the device.

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
        command = command.encode()

        self.log.debug("> %s", command)
        try:
            self.transport.write(command)
        except Exception as error:
            self.log.warning(
                "No transport found, unable to send command. error: %s", str(error)
            )

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

    def attenuation_to_volume(self, value):
        """Convert a native attenuation value to a volume value.

        Takes an attenuation in dB from the Anthem (-90 to 0) and converts it
        into a normal volume value (0-100).

            :param arg1: attenuation in dB (negative integer from -90 to 0)
            :type arg1: int

        returns an integer value representing volume
        """
        try:
            return round((90.00 + int(value)) / 90 * 100)
        except ValueError:
            return 0

    def volume_to_attenuation(self, value):
        """Convert a volume value to a native attenuation value.

        Takes a volume value and turns it into an attenuation value suitable
        to send to the Anthem AVR.

            :param arg1: volume (integer from 0 to 100)
            :type arg1: int

        returns a negative integer value representing attenuation in dB
        """
        try:
            return round((value / 100) * 90) - 90
        except ValueError:
            return -90

    @property
    def attenuation(self):
        """Current volume attenuation in dB (read/write).

        You can get or set the current attenuation value on the device with this
        property.  Valid range from -90 to 0.

        :Examples:

        >>> attvalue = attenuation
        >>> attenuation = -50
        """
        try:
            return int(self._Z1VOL)
        except ValueError:
            return -90
        except NameError:
            return -90

    @attenuation.setter
    def attenuation(self, value):
        if isinstance(value, int) and -90 <= value <= 0:
            self.log.debug("Setting attenuation to %s", str(value))
            self.command("Z1VOL" + str(value))

    @property
    def volume(self):
        """Current volume level (read/write).

        You can get or set the current volume value on the device with this
        property.  Valid range from 0 to 100.

        :Examples:

        >>> volvalue = volume
        >>> volume = 20
        """
        return self.attenuation_to_volume(self.attenuation)

    @volume.setter
    def volume(self, value):
        if isinstance(value, int) and 0 <= value <= 100:
            self.attenuation = self.volume_to_attenuation(value)

    @property
    def volume_as_percentage(self):
        """Current volume as percentage (read/write).

        You can get or set the current volume value as a percentage.  Valid
        range from 0 to 1 (float).

        :Examples:

        >>> volper = volume_as_percentage
        >>> volume_as_percentage = 0.20
        """
        volume_per = self.volume / 100
        return volume_per

    @volume_as_percentage.setter
    def volume_as_percentage(self, value):
        if isinstance(value, float) or isinstance(value, int):
            if 0 <= value <= 1:
                value = round(value * 100)
                self.volume = value

    #
    # Internal assistant functions for unified handling of boolean
    # properties that are read/write
    #

    def _get_boolean(self, key):
        keyname = "_" + key
        try:
            value = getattr(self, keyname)
            return bool(int(value))
        except ValueError:
            return False
        except AttributeError:
            return False

    def _set_boolean(self, key, value):
        if value is True:
            self.command(key + "1")
        else:
            self.command(key + "0")

    #
    # Boolean properties and corresponding setters
    #

    @property
    def power(self):
        """Report if device powered on or off (read/write).

        Returns and expects a boolean value.
        """
        return self._get_boolean("Z1POW")

    @power.setter
    def power(self, value):
        self._set_boolean("Z1POW", value)
        self.query("Z1POW")

    @property
    def txstatus(self):
        """Current TX Status of the device (read/write).

        When enabled, all commands, status changes, and control information
        are reported through the Ethernet and RS-232 connections.  Do not
        disable this setting, the anthemav package requires it.

        It is explicitly set to True whenever this module connects to the AVR,
        but I'll still let you disable it though, because I believe in aiming
        loaded guns right at my own feet.

            :param arg1: setting
            :type arg1: boolean
        """
        return self._get_boolean("ECH")

    @txstatus.setter
    def txstatus(self, value):
        self._set_boolean("ECH", value)

    @property
    def standby_control(self):
        """Current Standby IP Control of the device (read/write).

        When disabled, the AVM/MRX goes into a low-consumption standby mode and
        does not sense IP commands while in it. To make it respond to a
        power-on command or to keep DTS Play-Fi connected to the network so it
        can be used immediately after power- on, enable this setting.

            :param arg1: setting
            :type arg1: boolean
        """
        return self._get_boolean("SIP")

    @standby_control.setter
    def standby_control(self, value):
        self._set_boolean("SIP", value)

    @property
    def arc(self):
        """Current ARC (Anthem Room Correction) on or off (read/write)."""
        return self._get_boolean("Z1ARC")

    @arc.setter
    def arc(self, value):
        self._set_boolean("Z1ARC", value)

    @property
    def mute(self):
        """Mute on or off (read/write)."""
        return self._get_boolean("Z1MUT")

    @mute.setter
    def mute(self, value):
        self._set_boolean("Z1MUT", value)
        # Query mute because the AVR doesn't always return back the state
        # (eg: after power on without changing the volume first)
        self.query("Z1MUT")

    #
    # Read-only text properties
    #

    @property
    def model(self):
        """Device Model Name (read-only)."""
        return self._IDM or "Unknown Model"

    @property
    def swversion(self):
        """Software version (read-only)."""
        return self._IDS or "Unknown Version"

    @property
    def region(self):
        """Region (read-only)."""
        return self._IDR or "Unknown Region"

    @property
    def build_date(self):
        """Software build date (read-only)."""
        return self._IDB or "Unknown Build Date"

    @property
    def hwversion(self):
        """Hardware version (read-only)."""
        return self._IDH or "Unknown Version"

    @property
    def macaddress(self):
        """Network MCU MAC address (read-only)."""
        return self._IDN or self._EMAC or self._WMAC or EMPTY_MAC

    @property
    def audio_input_name(self):
        """Current audio input format short description (read-only)."""
        return self._Z1AIN or "Unknown"

    @property
    def audio_input_ratename(self):
        """Current audio input format sample or bit rate (read-only)."""
        return self._Z1AIR or "Unknown"

    #
    # Read-only raw numeric properties
    #

    def _get_integer(self, key):
        keyname = "_" + key
        if hasattr(self, keyname):
            value = getattr(self, keyname)
        try:
            return int(value)
        except ValueError:
            return

    @property
    def dolby_dialog_normalization(self):
        """Query Dolby Digital dialog normalization amount (read-only).

        Returns value in dB of normalization (if applicable).
        """
        return self._get_integer("Z1DIA")

    @property
    def horizontal_resolution(self):
        """Query active horizontal video resolution (in pixels)."""
        return self._get_integer("Z1IRH")

    @property
    def vertical_resolution(self):
        """Query active vertical video resolution (in pixels)."""
        return self._get_integer("Z1IRV")

    @property
    def audio_input_bitrate(self):
        """Query audio input bitrate (in kbps).

        For Analog/PCM inputs this is equal to the sample rate multiplied by
        the bit depth and the number of channels.
        """
        return self._get_integer("Z1BRT")

    @property
    def audio_input_samplerate(self):
        """Query audio input sampling rate (kHz)."""
        return self._get_integer("Z1SRT")

    #
    # Helper functions for working with raw/text multi-property items
    #
    #
    def _get_multiprop(self, key, mode="raw"):
        keyname = "_" + key

        if hasattr(self, keyname):
            rawvalue = getattr(self, keyname)
            value = rawvalue

            if key in LOOKUP:
                if rawvalue in LOOKUP[key]:
                    value = LOOKUP[key][rawvalue]

            if mode == "raw":
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
        """Current front panel brightness value (int 0-3) (read-write).

        0=off, 1=low, 2=medium, 3=high
        """
        return self._get_multiprop("FPB", mode="raw")

    @property
    def panel_brightness_text(self):
        """Current front panel brighness value (str) (read-only)."""
        return self._get_multiprop("FPB", mode="text")

    @panel_brightness.setter
    def panel_brightness(self, number):
        if isinstance(number, int):
            if 0 <= number <= 3:
                self.log.debug("Switching panel brightness to %s", str(number))
                self.command("FPB" + str(number))

    @property
    def audio_listening_mode_list(self):
        """List of available listening mode"""
        if any(m in self.model for m in ALM_RESTRICTED_MODEL):
            return [LOOKUP["Z1ALM"][s] for s in ALM_RESTRICTED]
        return list(ALM_NUMBER.keys())

    @property
    def audio_listening_mode(self):
        """Current audio listening mode (00-16) (read-write).

        Audio Listening Mode: 00=None, 01=AnthemLogic-Movie,
        02=AnthemLogic-Music, 03=PLIIx Movie, 04=PLIIx Music, 05=Neo:6 Cinema,
        06=Neo:6 Music, 07=All Channel Stereo*, 08=All-Channel Mono*, 09=Mono*,
        10=Mono-Academy*, 11=Mono(L)*, 12=Mono(R)*, 13=High Blend*, 14=Dolby
        Surround, 15=Neo:X-Cinema, 16=Neo:X-Music, na=cycle to next applicable,
        pa=cycle to previous applicable.  *Applicable to 2-channel source only.
        Some options are not available in all models or under all
        circumstances.
        """
        return self._get_multiprop("Z1ALM", mode="raw")

    @property
    def audio_listening_mode_text(self):
        """Current audio listening mode (str) (read-only)."""
        return self._get_multiprop("Z1ALM", mode="text")

    @audio_listening_mode.setter
    def audio_listening_mode(self, number):
        if isinstance(number, int):
            if 0 <= number <= 16:
                self.log.debug("Switching audio listening mode to %s", number)
                self.command("Z1ALM" + str(number).zfill(2))

    @audio_listening_mode_text.setter
    def audio_listening_mode_text(self, text):
        self.log.debug("Switching audio listening mode to %s", text)
        if text in ALM_NUMBER:
            self.command(f"Z1ALM{ALM_NUMBER[text]:02d}")

    @property
    def dolby_dynamic_range(self):
        """Current Dolby Dynamic Range setting (0-2) (read-write).

        Applies to Dolby Digital 5.1 source only.

        0=Normal, 1=Reduced, 2=Late Night.
        """
        return self._get_multiprop("Z1DYN", mode="raw")

    @property
    def dolby_dynamic_range_text(self):
        """Current Dolby Dynamic Range setting (str) (read-only)."""
        return self._get_multiprop("Z1DYN", mode="text")

    @dolby_dynamic_range.setter
    def dolby_dynamic_range(self, number):
        if isinstance(number, int):
            if 0 <= number <= 2:
                self.log.debug("Switching Dolby dynamic range to %s", str(number))
                self.command("Z1DYN" + str(number))

    #
    # Read-only properties with raw and text options
    #

    @property
    def video_input_resolution(self):
        """Current video input resolution (0-14) (read-only).

        0=no input, 1=other, 2=1080p60, 3=1080p50, 4=1080p24, 5=1080i60,
        6=1080i50, 7=720p60, 8=720p50, 9=576p50, 10=576i50, 11=480p60,
        12=480i60, 13=3D, 14=4k
        """
        return self._get_multiprop("Z1VIR", mode="raw")

    @property
    def video_input_resolution_text(self):
        """Current video input resolution (str) (read-only)."""
        return self._get_multiprop("Z1VIR", mode="text")

    @property
    def audio_input_channels(self):
        """Current audio input channels (0-7) (read-only).

        0=no input, 1=other, 2=mono (center channel only), 3=2-channel,
        4=5.1-channel, 5=6.1-channel, 6=7.1-channel, 7=Atmos
        """
        return self._get_multiprop("Z1AIC", mode="raw")

    @property
    def audio_input_channels_text(self):
        """Current audio input channels (str) (read-only)."""
        return self._get_multiprop("Z1AIC", mode="text")

    @property
    def audio_input_format(self):
        """Current audio input format (0-6) (read-only).

        0=no input, 1=Analog, 2=PCM, 3=Dolby, 4= DSD, 5=DTS, 6=Atmos.
        """
        return self._get_multiprop("Z1AIF", mode="raw")

    @property
    def audio_input_format_text(self):
        """Current audio input format (str) (read-only)."""
        return self._get_multiprop("Z1AIF", mode="text")

    #
    # Input number and lists
    #

    @property
    def input_list(self):
        """List of all enabled inputs."""
        return list(self._input_numbers.keys())

    @property
    def input_name(self):
        """Name of currently active input (read-write)."""
        return self._input_names.get(self.input_number, "Unknown")

    @input_name.setter
    def input_name(self, value):
        number = self._input_numbers.get(value, 0)
        if number > 0:
            self.input_number = number

    @property
    def input_number(self):
        """Number of currently active input (read-write)."""
        return self._get_integer("Z1INP")

    @input_number.setter
    def input_number(self, number):
        if isinstance(number, int):
            if 1 <= number <= 99:
                self.log.debug("Switching input to %s", str(number))
                self.command(f"Z1INP{number}")

    #
    # Miscellany
    #

    @property
    def dump_rawdata(self):
        """Return contents of transport object for debugging forensics."""
        if hasattr(self, "transport"):
            attrs = vars(self.transport)
            return ", ".join("%s: %s" % item for item in attrs.items())

    @property
    def test_string(self):
        """I really do."""
        return "I like cows"
