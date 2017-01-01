import argparse
import asyncio
import anthemav
import logging

log = logging.getLogger(__name__)

@asyncio.coroutine
def console(loop):
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
        log.info('Callback invoked: %s' % message)

    host = args.host
    port = int(args.port)

    log.info('Connecting to Anthem AVR at %s:%i' % (host, port))

    conn = yield from anthemav.Connection.create(host=host,port=port,loop=loop,update_callback=log_callback)

    log.info('Power state is '+str(conn.protocol.power))
    conn.protocol.power = True
    log.info('Power state is '+str(conn.protocol.power))

    yield from asyncio.sleep(2, loop=loop)

    log.info('Panel brightness (raw) is '+str(conn.protocol.panel_brightness))
    log.info('Panel brightness (text) is '+str(conn.protocol.panel_brightness_text))

def monitor():
    loop = asyncio.get_event_loop()
    asyncio.async(console(loop))
    loop.run_forever()
