######################
The Discovery Protocol
######################

The phantom camera offers a *discovery protocol*. This protocol is specifically designed to
limit the need to supply the IP address of the specific camera model manually to an application.
The IP of the camera will be *disovered automatically*.

This package provides both a command to run such a discovery process as a client as well as the
functionality to have the mock server reply to such a discovery request.

============
How it works
============

The discovery protocol works by having the client application send out a UDP broadcast to the
IP range, at which the cameras operate, containing the simple string "phantom?". *Every* phantom
camera, that receives this request will send a UDP response to the origin of the request. The
response is a string containing info about the camera protocol, that is used (PH16), hardware
version and serial number. The actual IP is not part of the response string, as it can be extracted
from the meta data of the response packet.

===========================
Sending a discovery request
===========================

.. highlight:: bash

To send a discovery request, use the *ph-discover* command. It will send a UDP broadcast wait
10 seconds for all incoming replies and then display them into the terminal ::

    ph-discover

The output for a single response will look like this ::

    # OUTPUT:
    # Phantom Camera using PH16:
    #       IP address:         127.0.0.1
    #       Listening on PORT:  7115
    #       Hardware version:   0.0.0.1
    #       Serial number:      66671929

Using the 10G connection
========================

In case the camera is connected using the 10G port, the *-x* flag has to be used for the
command, because then the discovery broadcast obviously has to be sent to a different
IP range. ::

    ph-discover -x





