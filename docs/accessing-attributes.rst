####################################################
Accessing attributes and configuration of the camera
####################################################

====================
The "getall" command
====================

.. highlight:: sh

For a rough overview of the current state and configuration of your camera, you can use the *ph-getall* command.
This command will fetch many essential attributes from the camera and display a nicely formatted table to
the command line, which will contain the name of the attribute, its value from the camera and a small description
of what this value tells us: ::

    ph-getall ip

For a more detailed info about the additional parameters use the "help" option ::

    ph-getall --help

