# Setup 
This code runs in linux ubuntu 20.04

https://www.wikihow.com/Install-Ubuntu-on-VirtualBox

make fullscreen

https://shaadlife.com/make-ubuntu-full-screen-on-virtualbox/


### Install python and pip
only follow step 1
https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-an-ubuntu-20-04-server


### Download Geckodriver
Install geckodriver from https://github.com/mozilla/geckodriver/releases/
make sure the geckodriver bin file is located in ```/usr/bin```
```bash
$cd /path to geckodriver
$sudo mv geckodriver /usr/bin/
```

### Configuring TOR

Download tor
```bash
$ sudo apt install tor
```
AND download via their website https://www.torproject.org/download/
extract to ```/home/usr/```

#### testing configuration

```bash 
from tbselenium.tbdriver import TorBrowserDriver
with TorBrowserDriver("/path/to/TorBrowserBundle/") as driver:
    driver.get('https://check.torproject.org')
```
```/path/to/TorBrowserBundle``` should look something like this ```home/usr/tor-browser_en-US/```

the folder contains a folder Browser, which contains the firefox binary.
if this did not get installed by ```$sudo apt install tor``` download and extract tor trough their website
    



