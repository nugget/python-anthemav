#!/usr/bin/env python3

import argparse
import asyncio
import anthemav
import logging

log = logging.getLogger(__name__)


async def test():
    parser = argparse.ArgumentParser(description=test.__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="IP or FQDN of AVR")
    parser.add_argument("--port", default="14999", help="Port of AVR")
    parser.add_argument("--verbose", "-v", action="count")

    args = parser.parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.ERROR

    logging.basicConfig(level=level)

    def log_callback(message):
        log.info("Callback invoked: %s" % message)

    host = args.host
    port = int(args.port)

    log.info("Connecting to Anthem AVR at %s:%i" % (host, port))

    conn = await anthemav.Connection.create(
        host=host, port=port, loop=loop, update_callback=log_callback
    )

    log.info("Power state is " + str(conn.protocol.power))
    conn.protocol.power = True
    log.info("Power state is " + str(conn.protocol.power))

    await asyncio.sleep(2, loop=loop)

    log.info("Panel brightness (raw) is " + str(conn.protocol.panel_brightness))
    log.info("Panel brightness (text) is " + str(conn.protocol.panel_brightness_text))

    log.info(
        "Video resolution (text) is " + str(conn.protocol.video_input_resolution_text)
    )
    log.info(
        "Audio input channels (text) is " + str(conn.protocol.audio_input_channels_text)
    )
    log.info(
        "Audio input format (text) is " + str(conn.protocol.audio_input_format_text)
    )
    log.info(
        "Audio listening mode (text) is " + str(conn.protocol.audio_listening_mode_text)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    loop.run_forever()
