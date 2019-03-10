##############################################
Simulating camera behaviour with a mock script
##############################################

This package also offers a mock command, which upon calling will start to simulate a phantom camera.
It will behave just like a phantom, except there doesnt need to be a ethernet cable, as it will be
running on the local IP *127.0.0.1* using the standard port *7115* for the control connection.

To start the mock service simply use the "ph-mock" command. ::

    ph-mock

The mock is mostly designed to test all the other commands within this package even without immediate access to
a real camera itself. For that just open two terminals and start the mock with the command above and run the other
commands in the second terminal.

==========
An example
==========

To view the main configuration of the camera and then grab a single frame just start up the mock as follows: ::

    # Terminal 1
    ph-mock

Then use the "ph-getall" command to display a table containing the most important attribute values and the "ph-img"
command to view an image ::

    # Terminal 2
    ph-getall 127.0.0.1 ;
    ph-img --format=P8 127.0.0.1

====================
Unsupported features
====================

The mock is still far from being a perfect emulation of a real camera, as it lacks a few features:

- Upon receiving possibly incorrect input, the returned error message is not reflective of what a real camera may respond. In some cases there may not even be an error message at all, but instead a crash of the mock script

- The UDP camera discovery protocol is not yet implemented at all

- Some attributes do not have an internal default value yet. Issuing a "get" command can result in the mock crashing

- 10G functionality is not yet implemented at all

- Setting different values to the attributes has no effect