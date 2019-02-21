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
phtest <IP ADDRESS>
```

#### Starting the mock server

To be able to test other services, that are supposed to make a connection with the phantom camera a mock server on the 
localhost address 127.0.0.1 and the phantom control interface port 7115 can be started by executing the script 
```bash
phmock
```
It simulates the behaviour of a real phantom camera

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