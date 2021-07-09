python-anthemav
===============

|Build Status| |GitHub release| |PyPI|

This is a Python package to interface with
`Anthem <http://www.anthemav.com>`__ AVM and MRX receivers and
processors. It uses the asyncio library to maintain an object-based
connection to the network port of the receiver with supporting methods
and properties to poll and adjust the receiver settings.

This package was created primarily to support an anthemav media_player
platform for the `Home Assistant <https://home-assistant.io/>`__
automation platform but it is structured to be general-purpose and
should be usable for other applications as well.

Important
~~~~~~~~~

This package will maintain a persistant connection to the network
control port which will prevent any other application from communicating
with the receiver. This includes the Anthem iOS and Android remote
control app as well as the ARC-2 room calibration software. You will
need to disable any application that is using the library in order to
run those other applications.

Requirements
------------

-  Python 3.5 or newer with asyncio
-  An Anthem MRX or AVM receiver or processor

Known Issues
------------

-  This has only been tested with an MRXx20 series receiver, although
   the Anthem protocol was largely unchanged from the MRXx10 series. It
   should work with the older units, but I’d appreciate feedback or pull
   requests if you encounter problems. It will definitely not work with
   the original MRXx00 units or the D2v models.

-  Only Zone 1 is currently supported. If you have other zones
   configured, this library will not allow you to inspect or control
   them. This is not an intractable problem, I just chose not to address
   that nuance in this initial release. It’s certainly feasible to add
   support but I am not settled on how that should be exposed in the
   internal API of the package.

-  I skipped over a lot of the more esoteric settings that are available
   (like toggling Dolby Volume on each input). If I passed over a
   setting that’s really important to you, please let me know and I’ll
   be happy to add support for it. Eventually I intend to cover the full
   scope of the Anthem API, but you know how it goes.

Installation
------------

You can, of course, just install the most recent release of this package
using ``pip``. This will download the more rececnt version from
`PyPI <https://pypi.python.org/pypi/anthemav>`__ and install it to your
host.

::

   pip install anthemav

If you want to grab the the development code, you can also clone this
git repository and install from local sources:

::

   cd python-anthemav
   pip install .

And, as you probably expect, you can live the developer’s life by
working with the live repo and edit to your heart’s content:

::

   cd python-anthemav
   pip install . -e

Testing
-------

The package installs a command-line tool which will connect to your
receiver, power it up, and then monitor all activity and changes that
take place. The code for this console monitor is in
``anthemav/tools.py`` and you can invoke it by simply running this at
the command line with the appropriate IP and port number that matches
your receiver and its configured port:

::

   anthemav_monitor --host 10.0.0.100 --port 14999

Helpful Commands
----------------

::

   sudo tcpflow -c port 14999

Interesting Links
-----------------

-  `Project Home <https://github.com/nugget/python-anthemav>`__
-  `API Documentation for Anthem Network
   Protocol <http://www.anthemav.com/downloads/MRX-x20-AVM-60-IP-RS-232.xls>`__
   (Excel Spreadsheet)
-  `Pictures of cats <http://imgur.com/r/cats>`__

Credits
-------

-  This package was written by David McNett.

   -  https://github.com/nugget
   -  https://keybase.io/nugget

How can you help?
-----------------

-  First and foremost, you can help by forking this project and coding.
   Features, bug fixes, documentation, and sample code will all add
   tremendously to the quality of this project.

-  If you have a feature you’d love to see added to the project but you
   don’t think that you’re able to do the work, I’m someone is probably
   happy to perform the directed development in the form of a bug or
   feature bounty.

-  If you’re anxious for a feature but it’s not actually worth money to
   you, please open an issue here on Github describing the problem or
   limitation. If you never ask, it’ll never happen

-  If you just want to thank me for the work I’ve already done, I’m
   happy to accept your thanks, gratitude, pizza, or bitcoin. My bitcoin
   wallet address can be on `Keybase <https://keybase.io/nugget>`__ or
   you can send me a donation via
   `PayPal <https://www.paypal.me/macnugget>`__.

-  Or, if you’re not comfortable sending me money directly, I’ll be
   nearly as thrilled (really) if you donate to `the
   ACLU <https://action.aclu.org/donate-aclu>`__,
   `EFF <https://supporters.eff.org/donate/>`__, or
   `EPIC <https://epic.org>`__ and let me know that you did.

.. |Build Status| image:: https://travis-ci.org/nugget/python-anthemav.svg?branch=master
   :target: https://travis-ci.org/nugget/python-anthemav
.. |GitHub release| image:: https://img.shields.io/github/release/nugget/python-anthemav.svg
   :target: https://github.com/nugget/python-anthemav/releases
.. |PyPI| image:: https://img.shields.io/pypi/v/anthemav.svg
   :target: https://pypi.python.org/pypi/anthemav
