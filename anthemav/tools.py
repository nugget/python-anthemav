"""Provides a raw console to test module and demonstrate usage."""
import argparse
import asyncio
import logging

import anthemav

__all__ = ('console', 'monitor')


@asyncio.coroutine
def console(loop, log):
    """Connect to receiver and show events as they occur.

    Pulls the following arguments from the command line (not method arguments):

    :param host:
        Hostname or IP Address of the device.
    :param port:
        TCP port number of the device.
    :param verbose:
        Show debug logging.
    """
    parser = argparse.ArgumentParser(description=console.__doc__)
    parser.add_argument('--host', default='127.0.0.1', help='IP or FQDN of AVR')
    parser.add_argument('--port', default='14999', help='Port of AVR')
    parser.add_argument('--verbose', '-v', action='count')

    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level)

    def log_callback(message):
        """Receives event callback from Anthem Protocol class."""
        log.info('Callback invoked: %s' % message)

    host = args.host
    port = int(args.port)

    log.info('Connecting to Anthem AVR at %s:%i' % (host, port))

    conn = yield from anthemav.Connection.create(
        host=host, port=port, loop=loop, update_callback=log_callback)

    log.info('Power state is '+str(conn.protocol.power))
    conn.protocol.power = True
    log.info('Power state is '+str(conn.protocol.power))

    yield from asyncio.sleep(2, loop=loop)

    log.info('Panel brightness (raw) is '+str(conn.protocol.panel_brightness))
    log.info('Panel brightness (text) is '+str(conn.protocol.panel_brightness_text))


def monitor():
    """Wrapper to call console with a loop."""
    log = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()
    asyncio.async(console(loop, log))
    loop.run_forever()
