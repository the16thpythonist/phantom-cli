###############
Getting started
###############

the *phantom-cli* package provides command line tools for testing and exploring the network
interface of `Vision Research Phantom Cameras <https://www.phantomhighspeed.com/products>`_.
This projects will only support cameras, that operate on the *PH16 camera protocol* as
specified in `this PDF <https://confluence.diamond.ac.uk/download/attachments/65899299/v16proto-2.3.pdf?version=1&modificationDate=1500390734000&api=v2>`_.

=============
Prerequisites
=============

Currently this project is only supported for unix environments and is only actively developed and
tested on Ubuntu 18.04 LTS. Although different UNIX and especially ubuntu distro's should work, it is
not guaranteed.

Furthermore this project works with Python >= 3.5.

And of course to be able to communicate with the camera, your machine needs a functioning ethernet interface.

============
Installation
============

.. highlight:: sh

It is strongly encouraged to install this package using *pip*, as it will automatically handle the
installation and setup of the commands provided by this package.::

    pip install phantom-cli

You can check, if the installation worked correctly, by attempting to execute one of the scripts ::

    ph-test --help

If there is no command by that name, try uninstalling and reinstalling the package using pip and super
user privileges.

============
The Hardware
============

Now it comes to setting up your PC to actually be able to communicate with the camera. The following section
will explain the general steps needed.

**Important note**: There are some cameras, that offer a 10G ethernet connection. These will have to
be treated differently and are not being addressed in the coming section. The following information refers
to a standard ethernet connection only!

1. First, you will have to configure the ethernet interface of your PC to the correct IP range, which the camera
also uses and expects.

Your ethernet interface should be set up to a **static IP 100.100.100.xxx**, replacing the x's with any valid number
you choose, for example 100.100.100.1. Additionally a **netmask of 100.100.255.255** is required.

2. If your ethernet is all set up and ready you can plug in the ethernet cable to the phantom camera!
Note that some cameras need some time to boot before, they are ready to communicate.

3. The final step is to identify the specific IP address of your camera. Usually the IP address is either printed on
a sticker located somewhere on the camera itself, or listed in the additional resources shipped with the camera.

Once you have the IP address of the camera, you can proceed and check the network connection using the
*ph-test* script. ::

    ph-test <PHANTOM IP>

If the connection to the Phantom can be established, the output of the script will tell you so.
In case there was a problem with the connection consider to turn on *the log messages* for further troubleshooting::

    ph-test --log=DEBUG <PHANTOM IP>

**Important note**: The "--log=DEBUG" option is also available for every other command in this package and might
come in handy, when troubleshooting or generally taking a closer look at the underlying protocols.