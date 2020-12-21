import serial


def get_port():
    #get specific port for TC based on HWID

def connect_TC():
    #start com serial connection and return serial object

def close_TC():
    #closes the serial connection

def wrap_cmd():
    #wrap commands with required bytes, see GC89800 protocol in manuals

def get_temp(s):
    #get current temperature

def set_temp(s, temp):
    #set temperautre

def log_temp():
    #log temperature in txt file
