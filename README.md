# Phantom camera command line tools

This package provides command line tools for interfacing with a phantom camera, using an ethernet connection/ network 
in general.

## Getting started

### prerequisites

This package uses python 3, so make sure python 3.5+ is installed on your system.
This package also uses the python package "matplotlib", which in turn relies on the python module 
"tkinter", which cannot be installed as a dependency, instead make sure to install it by typing into the 
terminal (on ubuntu):
```bash
sudo apt-get install python3-tk
```

### Installing

This package can be installed using the [Python Package Index(PyPi)](https://pypi.org/).
Simply type into the console:
```bash
pip install phantom-cli
```
If the installation works as intended, this python module will also add additional console commands, with which 
the phantom camera can be accessed. To test if the installation was successful type:
```bash
phtest --help
```
If no command with that name exists, try installing reinstalling the package using super user permissions
```bash
pip uninstall phantom-cli
sudo pip install phantom-cli
```

### First steps

#### Checking the connection

When connected to the phantom camera via an ethernet cable, execute the *phtest* command, using the IP address of your 
specific phantom camera model:
```bash
ph-test <IP ADDRESS>
```

For a more detailed information on how to use this package please visit the [Documentation](https://phantom-cli.readthedocs.io/en/latest/index.html)!



## Authors

* **Jonas Teufel** - *Initial work* - [the16thpythonist](https://github.com/the16thpythonist)

## License 

This project is licensed under the MIT License

## CHANGELOG

### 0.0.0.4 - Initial version
- set up the project skeleton, including the build and setup scripts and the folder structure
- class network.PhantomSocket as main wrapper for communicating with the phantom in the future
- class network.PhantomMockServer tcp server, which simulates a phantom camera operating on 127.0.0.1::7115
in the future
- script "phtest", which will be used to test the connection to the phantom camera.

### 0.0.0.5 - 21.02.2019
- class phantom.PhantomCamera, which represents the phantom camera and all its attributes
- class network.PhantomMockControlInterface used for the actual handling of the mock incoming requests, because 
the mock server has been rewritten with the "socketserver" module
- Implemented "get" handling for the mock server 
- script "phmock", which simply starts the mock server on 127.0.0.1 and the phantom port
- Implemented "get" functionality for PhantomSocket.

### 0.0.0.6 - 21.02.2019
- script "phget" to issue single get commands to the phantom camera

### 0.0.0.7 -23.02.2019
- class image.PhantomImage represents images takes from the phantom camera and handles the conversion 
between different formats, especially the transfer formats
- module command: This module handles the parsing of the phantom protocols own system of parameters in 
request and response messages 
- class phantom.PhantomDataTransferServer a server that gets opened by the client, to which the phantom 
can connect to as a client. This secondary channel will be used to transfer bulk data such as images.
- class phantom.PhantomDataTransferHandler a thread that will be created to handle the connection to the 
phantom data stream. Will receive a single image completely
- Added the functionality to recieve images to the PhantomSocket
- Added the functionality to respond to a img request to the mock. it will now send a sample jpg image from 
the project folder.

### 0.0.0.8 - 23.02.2019
- Fixed a bug with the scripts not being included into the pypi package

### 0.0.0.9 - 26.02.2019
- Fixed some additional bugs, while working with the actual camera, all previous programming was based on 
assumptions made from the used protocol

### 0.0.0.12 - 07.03.2019
- Implemented conversion from and to P8 and P10 image transfer formats in PhantomImage
- Implemented the P8 and P10 img transfer formats for the PhantomSocket.
- class command.ImgFormatsMap: static class, that maps the string and int representations of the image transfer formats
- script "phgetall", which will make multiple get request to the camera and then display a formatted listing of the most 
important attributes of the camera along with the descriptions
- script "phset", which can be used to modify attributes of the camera
- Set up documentation on "read the docs"

### 0.0.0.13 - 10.03.2019

- Added documentation to the scripts by adding a helpful "--help" text

### 0.0.0.14 - 10.05.2019

- Added a method for the PhantomImage and PhantomCamera to create random images instead of using always the 
one static image.
- Added a parameter to the phmock script to specify a image policy. Either static sample or randomly created image.
- Fixed the P10 Encoding algorithm, so that all image conversion tests now pass

### 0.0.0.15 - 10.05.2019

- Fixed, that images were being displayed sideways
- Fixed receiving of images using the 10G interface
- Added Documentation to the "data.py" module
- Added correct behaviour to the ximg handling of the mock, when multiple frames are requested

### 0.0.0.16 - 20.05.2019

- Added full support for the discovery protocol:
    - Mock: The mock will now additionally start a UDP server listening on the port 7380 for incoming discovery 
    requests. If a valid request has been received it will respond with a string containing the control port on which 
    it is listening, the "info.hwver" value and the serial number of the mock camera model. Everything as specified for 
    the PH16 camera protocol
    - PhantomSocket: Added an additional method "discover" which will sent out a discovery request broadcast into the 
    network and then return a list of dicts. One dict containing all the relevant info for one received response to the 
    discovery request 
- Added an additional command line tool "ph-discover", which will sent a 
discovery request into the network

### 0.0.0.18 - 27.05.2019

- Added 10G ethernet connection support for the ph-discover command, as 
a different IP range is needed then.
- Updated the documentation

### 0.1.0 - 14.07.2019

- Added the "ph-mode" command, which can be used to switch the mode of the phantom camera between 
"standard - high speed" and "normal - binned"
- Added the "P12L" transfer format support as a possibility for both the main socket object as well as the mock
