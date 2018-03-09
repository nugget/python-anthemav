#!/usr/bin/env python3

# to run this test you need to add the parent folder path to your PYTHONPATH. See the following example
# Use this command if your terminal is in the parent folder: PYTHONPATH=/path/to/parent/folder python tests/fulltests.py
# Use this command if your terminal is in the tests folder: PYTHONPATH=/path/to/parent/folder python fulltests.py

import asyncio
import unittest
import logging
import settings

import anthemav

@asyncio.coroutine
def test():
    log = logging.getLogger(__name__)

    def log_callback(message):
        log.info('Callback invoked: %s' % message)

    host = settings.IPADDRESS
    port = settings.PORT

    log.info('Connecting to Anthem AVR at %s:%s' % (host, port))

    # conn = yield from anthemav.Connection.create(host=host,port=port,loop=loop,update_callback=log_callback,auto_reconnect=False)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
