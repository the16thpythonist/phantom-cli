###############
Grabbing images
###############

====================================
Grabbing single frames using the img
====================================

it is important to note, that some cameras offer the possibility to transfer frames either over the "regular" ethernet
port or the 10G ethernet connection. The following command however does not support the 10G connection and thus may
be relatively slow, as it is only designed for testing purposes.

According to the *PH16 camera protocol* the image is not being retrieved over the main network socket used to send and
receive control commands. Instead a secondary channel for data transfer only is established by opening a server on the
control unit (your device running the script) and waiting to the camera to connect to it.

Then according to the different transfer protocols the raw frame is transmitted using a fixed amount of bytes for each
pixel, without overhead.

As soon as the whole data has been retrieved, another window will open displaying the image.

Use the "ph-img" command to grab a single frame, by specifying the IP address. Additionally you may specify
the transfer format to be used as the amount of bytes used per pixel will influence the data transfer time. ::

    ph-img --format=<FORMAT IDENTIFIER> <PHANTOM IP>

The three transfer formats and their respective pixel encoding size:

- *P10*: 32 bit / 4 byte per pixel

- *P16*: 16 bit / 2 byte per pixel

- *P8*: 8 bit / 1 byte per pixel

