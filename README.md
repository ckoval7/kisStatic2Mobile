# kisStatic2Mobile
 TCP location updating proxy for Kismet Remote

 This software sets up a proxy server between your Kismet remote capture source
and Kismet Server. This proxy looks for data report packets with static location
information and updates them with location provided by gpsd.

It has been tested to work with:

    * kismet_cap_linux_wifi
    * kismet_cap_linux_bluetooth
    * kismet_cap_ubertooth_one
    * kismet_cap_bladerf_wiphy
    * kismet_cap_nrf_52840

Please help by testing other capture sources!

# Installation

    * [Set up gpsd per your OS's Instructions](https://gpsd.gitlab.io/gpsd/installation.html)
    * You'll need the gpsd-py3 library. Run `pip3 install gpsd-py3`

# Usage

  These instructions assume your Kismet server is properly configured to receive
  remote connections.

  The proxy should run on the same device as your capture sources and gps.
  By default the proxy will listen on `127.0.0.1:3500`

  1. Activate Kismet server, make note of the IP. In this example, we'll use `172.16.0.100`
  1. On the remote host, run kisstatic2mobile.py:

      Example:
      `kisstatic2mobile.py --send 172.16.0.100:3501`
  1. Activate your capture sources (up to 5 at once, but the limit can be adjusted in the code)
      Make sure to define a static location so the proxy has a location field to edit.

      Examples:
      * `kismet_cap_linux_wifi --connect 127.0.0.1:3500 --tcp --fixed-gps 39.5,-75.5 --source wlan1:name=rpiMobile-wifi`
      * `kismet_cap_linux_bluetooth --connect 127.0.0.1:3500 --tcp --fixed-gps 39.5,-75.5 --source hci0:name=rpiMobile-bt`

  ```
  Usage: kisstatic2mobile.py [options]

  Options:
    -h, --help        show this help message and exit
    --listen=IP:PORT  IP Address to listen to. Default 127.0.0.1:3500
    --send=IP:PORT    Kismet Server Address. Default 127.0.0.1:3501
  ```
