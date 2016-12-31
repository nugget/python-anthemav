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

### Important
This package will maintain a persistant connection to the network control port
which will prevent any other application from communicating with the receiver.
This includes the Anthem iOS and Android remote control app as well as the 
ARC-2 room calibration software.  You will need to disable any application that
is using the library in order to run those other applications.

## Requirements

- Python 3.4 or 3.5 with asyncio
- An Anthem MRX or AVM receiver or processor

## Known Issues

- This has only been tested with an MRXx10 series receiver, although the Anthem
  protocol was largely unchanged from the MRXx00 series.  It should work with
  the older units, but I'd appreciate feedback or pull requests if you
  encounter problems

- Only Zone 1 is currently supported.  If you have other zones configured, this
  library will not allow you to inspect or control them.  This is not an
  intractable problem, I just chose not to address that nuance in this initial
  release.  It's certainly feasible to add support but I am not settled on how
  that should be exposed in the internal API of the package.

- I skipped over a lot of the more esoteric settings that are available (like
  toggling Dolby Volume on each input).  If I passed over a setting that's
  really important to you, please let me know and I'll be happy to add support
  for it.  Eventually I intend to cover the full scope of the Anthem API, but
  you know how it goes.

## Related Links

- [API Documentation for Anthem Network
  Protocol](http://www.anthemav.com/downloads/MRX-x20-AVM-60-IP-RS-232.xls)
  (Excel Spreadsheet)

## Credits

- This pacakge was written by David McNett.
  - https://github.com/nugget
  - https://keybase.io/nugget

## How can you help?

- First and foremost, you can help by forking this project and coding.  Features,
  bug fixes, documentation, and sample code will all add tremendously to the
  quality of this project.

- If you have a feature you'd love to see added to the project but you don't
  think that you're able to do the work, I'm someone is probably happy to
  perform the directed development in the form of a bug or feature bounty.

- If your anxious for a feature but it's not actually worth money to you,
  please open an issue here on Github describing the problem or limitation.  If
  you never ask, it'll never happen

- If you just want to thank me for the work I've already done, I'm happy to
  accept your thanks, gratitude, pizza, or bitcoin.  My bitcoin wallet address
  can be on [Keybase](https://keybase.io/nugget).  Or, I'll be nearly as
  thrilled (really) if you donate to [the
  ACLU](https://action.aclu.org/donate-aclu), or
  [EFF](https://supporters.eff.org/donate/) and you let me know that you did.
