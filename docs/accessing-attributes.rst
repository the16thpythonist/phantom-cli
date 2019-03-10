####################################################
Accessing attributes and configuration of the camera
####################################################

==================
Reading attributes
==================

The "getall" command
====================

.. highlight:: sh

For a rough overview of the current state and configuration of your camera, you can use the *ph-getall* command.
This command will fetch many essential attributes from the camera and display a nicely formatted table to
the command line, which will contain the name of the attribute, its value from the camera and a small description
of what this value tells us: ::

    ph-getall <PHANTOM IP>

For a more detailed info about the additional parameters use the "help" option ::

    ph-getall --help

The "get" command
=================

Of course the camera has far more attributes than listed by the "ph-getall" command. To get a full list of all the
available attributes check `this PDF <https://confluence.diamond.ac.uk/download/attachments/65899299/v16proto-2.3.pdf?version=1&modificationDate=1500390734000&api=v2>`_ .
It contains a full list of the names and descriptions of all the attributes and also whether they are read only ore
configurable.

Use the get command by specifying the Phantom IP and the name of the attribute to retrieve: ::

    ph-get <PHANTOM IP> <ATTRIBUTE NAME>


=========================
Changing Attribute Values
=========================

The "set" command
=================

Some values such as the camera's expore time for example can be written with custom values, before actually capturing
images.

Use the "ph-set" command by specifying the IP address of the Phantom, the name of the attribute to modify and the new
value to be assigned to it: ::

    ph-set <PHANTOM IP> <ATTRIBUTE NAME> <VALUE>

