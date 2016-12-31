# python-anthemav

[![Build Status](https://travis-ci.org/nugget/python-anthemav.svg?branch=master)](https://travis-ci.org/nugget/python-anthemav)

This is a Python package to interface with [Anthem](http://www.anthemav.com)
AVM and MRX receivers and processors.  It uses the asyncio library to maintain
an object-based connection to the network port of the receiver with supporting
methods and properties to poll and adjust the receiver settings.

This package was created primarily to support an anthemav media_player platform
for the [Home Assistant](https://home-assistant.io/) automation platform but it
is structured to be general-purpose and should be usable for other applications
as well.

## Requirements

- Python 3.4 or 3.5 with asyncio
- An Anthem MRX or AVM receiver or processor

## Known Issues

- This has only been tested with an MRXx10 series receiver, although the Anthem
  protocol was largely unchanged from the MRXx00 series.  It should work with
  the older units, but I'd appreciate feedback or pull requests if you
  encounter problems
