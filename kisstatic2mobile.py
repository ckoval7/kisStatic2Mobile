#!/usr/bin/env python3

# KisStatic2Mobile - TCP Location updating proxy for Kismet Remote
# Copyright (C) 2021 Corey Koval
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import socket, struct, gpsd, threading
from _thread import start_new_thread
from optparse import OptionParser
from time import sleep
import kismet_pb2 as kismet
import datasource_pb2 as kds
import linuxbluetooth_pb2 as lbt

print_lock = threading.Lock()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def kismet_adler32(data):
    i = 0
    charoffset = 0
    s1 = 0
    s2 = 0

    data_len = len(data)

    if data_len < 4:
        return 0

    for i in range(0, data_len-4, 4):
        s2 += 4 * (s1 + data[i]) + 3 * data[i+1] + 2 * data[i+2] + data[i+3] + 10 * charoffset
        s1 += data[i] + data[i+1] + data[i+2] + data[i+3] + 4 * charoffset

    for i in range(i+4, data_len):
        s1 += data[i] + charoffset
        s2 += s1

    output = ((s1 & 0xffff) + (s2 << 16)) & 0xffffffff
    return output

# Safe Print
def s_print(*a, **b):
    with print_lock:
        print(*a, **b)

def location_updater(c):
    try:
        # c, addr = lsock.accept()
        kserv = (kserv_ip, int(kserv_port))
        ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        notconnected = True
        while notconnected:
            try:
                s_print("Connecting to Kismet server.")
                ssock.connect(kserv)
                notconnected = False
            except ConnectionRefusedError:
                s_print("Kismet Server offline. Waiting 5 seconds...")
                sleep(5)

        while True:
            data = bytearray(c.recv(buffer))
            location = gpsd.get_current()
            s_print(f"Passing {len(data)} Bytes")
            # try:
            for byte in range(len(data)):
                command = data[byte:byte+13].decode('utf-8', 'backslashreplace')
                if command == "KDSDATAREPORT" or command == "LBTDATAREPORT":
                    data_size = struct.unpack('!I', data[byte-6:byte-2])[0]
                    data_range = data[byte-2:byte+data_size-2]
                    original_checksum = struct.unpack('!I', data[byte-10:byte-6])[0]
                    if original_checksum == kismet_adler32(data_range):
                        kis_command = kismet.Command()
                        kis_command.ParseFromString(data_range)

                        if command == "KDSDATAREPORT":
                            kis_content = kds.DataReport()
                        elif command == "LBTDATAREPORT":
                            kis_content = lbt.LinuxBluetoothDataReport()

                        kis_content.ParseFromString(kis_command.content)
                        # print(f"Squence_number: {kis_command.seqno}")
                        try:
                            kis_content.gps.lat = location.lat
                            kis_content.gps.lon = location.lon
                            kis_content.gps.alt = location.alt
                            kis_command.content = kis_content.SerializeToString()
                            data_out = kis_command.SerializeToString()
                            data[byte-2:byte+data_size-2] = data_out
                            data[byte-10:byte-6] = struct.pack('!I', kismet_adler32(data_out))
                        except UserWarning:
                            s_print("No GPS Data, not altering location.")

            ssock.send(data)
            c.send(ssock.recv(buffer))
            # total_data += len(data)
            del data
    except Exception as e:
        print(e)

    c.close()


if __name__ == '__main__':
    ###############################################
    # Help info printed when calling the program
    ###############################################
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("--listen", dest="listen_ipport", help="IP Address to listen to. Default 127.0.0.1:3500",
    metavar="IP:PORT", type="str", default="127.0.0.1:3500")
    parser.add_option("--send", dest="send_ipport", help="Kismet Server Address. Default 127.0.0.1:3501",
    metavar="IP:PORT", type="str", default="127.0.0.1:3501")
    # parser.add_option("--debug", dest="debugging", help="Does not clear the screen. Useful for seeing errors and warnings.",
    # action="store_true")
    (options, args) = parser.parse_args()
    max_connections = 5

    try:
        # Connect to the local gpsd
        print("Connecting to GPSd...")
        gpsd.connect()

        listen_ip, listen_port = options.listen_ipport.split(':', 1)
        print(f"Listening for connections on {options.listen_ipport}")
        kserv_ip, kserv_port = options.send_ipport.split(':', 1)
        print(f"Kismet Server: {options.send_ipport}")
        print("Remember to set a fixed location when connecting your sources!")

        # TCP Window size
        buffer = (2**16 - 1) * (2**11)

        c = None
        total_data = 0


        lsock.bind((listen_ip, int(listen_port)))
        lsock.listen(max_connections)

        while True:
            c, addr = lsock.accept()
            s_print('Connected to :', addr[0], ':', addr[1])
            start_new_thread(location_updater, (c,))

    except KeyboardInterrupt:
        lsock.close()

    except Exception as e:
        lsock.close()
        print(e)
