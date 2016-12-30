import argparse
import asyncio
import logging

from .protocol import create_anthemav_reader

def console():
    parser = argparse.ArgumentParser(description=console.__doc__)
    parser.add_argument('--host', default='127.0.0.1', help='IP or FQDN of AVR')
    parser.add_argument('--port', default='14999', help='Port of AVR')
    parser.add_argument('--verbose', '-v', action='count')

    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    logging.basicConfig(level=level)

    loop = asyncio.get_event_loop()

    def print_callback(callerobj,message):
        print(message)

    conn = create_anthemav_reader(args.host,args.port,print_callback,loop=loop)

    loop.create_task(conn)
    loop.run_forever()
