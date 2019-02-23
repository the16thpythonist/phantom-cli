# Phantom camera command line tools

This package provides command line tools for interfacing with a phantom camera, using an ethernet connection/ network 
in general.

## Getting started

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

#### Starting the mock server

To be able to test other services, that are supposed to make a connection with the phantom camera a mock server on the 
localhost address 127.0.0.1 and the phantom control interface port 7115 can be started by executing the script 
```bash
ph-mock
```
It simulates the behaviour of a real phantom camera

#### Reading phantom attributes

To read attributes of the phantom camera use the phget script
```bash
ph-get <IP ADDRESS> <ATTRIBUTE>
```
Replace ATTRIBUTE with the name of the attribute/structure to be read from the phantom

#### Grabbing an image from the camera

To grab a single image frame from the camera use the following command, replacing the YOUR OWN IP ADDRESS with the 
ip address, the phantom told you to use.
```bash
ph-img <IP ADDRESS> -i <YOUR OWN IP ADDRESS>
```
If everything works correctly the result will be the image showing as a separate on the screen

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