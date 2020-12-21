import serial
import serial.tools.list_ports
import logging
import threading
import struct

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target = t, args = args)
        self.start()

tc_hwid = "USB VID:PID=0403:6001 SER=AI02KU1BA"
lock = threading.Lock()

def get_port():
    #get specific port for TC based on HWID
    logging.info("Looking for ports: ")
    ports = serial.tools.list_ports.comports()
    if (ports != []):
        for port, desc, hwid in sorted(ports):
        
            logging.info("{}: {} [{}]".format(port, desc, hwid))
            if (hwid == tc_hwid):
                logging.info("Found port of temperature controller: " + port)
                return port
    else:
        logging.info("No port found for temperature controller")

def connect_tc():
    #start com serial connection and return serial object
    logging.info("Connecting to tc")

def close_tc():
    #closes the serial connection
    logging.info("Closing connection to tc")

def toggle_tc(s):
    s.write('s'.encode('latin-1'))

def mb_cmd(cmd):
    #formatting multibyte command, see GC89800 protocol in manuals
    logging.info("Formatting command:")

    accepted_cmds = {'GVT', 'GVS', 'SVS'}
    
    cmd_string = cmd[:3]

    if (cmd_string in accepted_cmds):
        btf = len(cmd) + 3
        xbtf = 255 - btf
        end = '>'
        transmission = chr(btf) + chr(xbtf) + cmd
        transmission += struct.pack('>H', sum(transmission.encode('latin-1'))).decode('latin-1') + end
        data = transmission.encode('latin-1')
        logging.info(data)
        return data
    else:
        logging.info("Not a cmd")
    
def get_temp(s):
    #get current temperature
    logging.info("Getting temperature")
    

def set_temp(s, temp):
    #set temperautre
    logging.info("Setting temperature")

def start_log_temp():
    #log temperature in txt file
    logging.info("Starting temperature log")

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    get_port()
    mb_cmd('SVS4000')
