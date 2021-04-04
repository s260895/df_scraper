# Setup 
This code runs in linux ubuntu 20.04


### Download Geckodriver
Install geckodriver from https://github.com/mozilla/geckodriver/releases/
make sure the geckodriver bin file is located in ```/usr/bin```

### Configuring TOR

Download tor
```bash
$ sudo apt tor
```
or download via their website

#### testing configuration

```bash 
from tbselenium.tbdriver import TorBrowserDriver
with TorBrowserDriver("/path/to/TorBrowserBundle/") as driver:
    driver.get('https://check.torproject.org')
```
```/path/to/TorBrowserBundle``` should look something like this ```home/usr/tor-browser_en-US/```

the folder contains a folder Browser, which contains the firefox binary.
if this did not get installed by ```$sudo apt tor``` download and extract tor trough their website
    



