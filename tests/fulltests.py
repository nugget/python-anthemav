#!/usr/bin/env python3

import asyncio
import unittest
import logging

import anthemav


@asyncio.coroutine
def test():
    log = logging.getLogger(__name__)

    def log_callback(message):
        log.info("Callback invoked: %s" % message)

    host = "127.0.0.1"
    port = 14999

    log.info("Connecting to Anthem AVR at %s:%i" % (host, port))

    # conn = yield from anthemav.Connection.create(host=host,port=port,loop=loop,update_callback=log_callback,auto_reconnect=False)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
