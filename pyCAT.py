import serial
import serial.tools.list_ports
import time
import re
import csv
import threading
from datetime import datetime
import logging

# Configure error logging
logging.basicConfig(filename=f'error.log', level=logging.ERROR, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Add console handler for error logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
logging.getLogger().addHandler(console_handler)

# Configure info logging
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler(f'info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
info_logger.addHandler(info_handler)

sc_temp = b'\x06\xf9GVT\x01\xf0>'
sc_setpoint = b'\x06\xf9GVS\x01\xef>'
temp = 0

def available_ports():
    ports = serial.tools.list_ports.comports()
    for port, _, hwid in sorted(ports):
        if hwid == "USB VID:PID=0403:6001 SER=AI02KU1BA":
            return port

def connect_tc():
    port = available_ports()
    if port:
        return serial.Serial(port, 250000, timeout=0.5)
    return None

def send_serial_command(s, command, attempts=2, response_length=15, sleep_duration=0.1):
    for _ in range(attempts):
        s.flushInput()
        s.write(command)
        time.sleep(sleep_duration)
        response = s.read(response_length).decode('latin-1')
        if response:
            return response
    return None

def get_temp(s):
    response = send_serial_command(s, sc_temp)
    if response:
        temp_match = re.findall(r"[-+]?\d*\.\d+|\d+", response)
        if temp_match:
            return float(temp_match[0])
    return None

def set_temp(s, temp):
    temp = round(temp*1.002, 2)
    digits = len(str(temp)) - 1
    frame_1 = 7 + digits
    frame_2 = 255 - frame_1
    frame = chr(frame_1) + chr(frame_2) + "SVS" + str(temp)

    total = frame + chr(2) + chr(sum(frame.encode("latin-1"))%256) + '>'

    send_serial_command(s, total.encode("latin-1"))

def get_set_temp(s):
    response = send_serial_command(s, sc_setpoint)
    if response:
        temp_match = re.findall(r"[-+]?\d*\.\d+|\d+", response)
        if temp_match:
            return float(temp_match[0])/1.002
    return None

def run_temp(s, final_temp, ramp_rate, soak_limit):
    info_logger.info("Starting temperature profile")
    logged_time = None
    # Overwrite existing temperature.csv
    with open('20241206_lot_r2_temperature.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Current Temp', 'Set Temp'])
    
    new_set_temp = None
    soak_limit = soak_limit * 60
    soak_time = 0
    stable_time = 5*60
    while True:
        current_temp = None
        current_set_temp = None

        for _ in range(3):
            current_temp = get_temp(s)
            if current_temp is not None:
                break
            logging.error("Failed to retrieve current temperature, retrying...")
        
        for _ in range(3):
            current_set_temp = get_set_temp(s)
            
            if current_set_temp is not None:
                break
            logging.error("Failed to retrieve set temperature, retrying...")
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if current_temp is not None and current_set_temp is not None:
            if new_set_temp is None:
                new_set_temp = current_temp
            if current_time != logged_time:
                with open('20241206_lot_r2_temperature.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([current_time, f"{current_temp:.2f}", f"{current_set_temp:.2f}"])
                    file.flush()
                if stable_time < 0:
                    if current_temp < (final_temp*0.997):
                        new_set_temp += ramp_rate/60
                        
                        set_temp(s, new_set_temp)
                    else:
                        set_temp(s, final_temp)
                        info_logger.info("Temperature reached final setpoint")
                        soak_time += 1
                        if soak_time > soak_limit:
                            break
                else:
                    stable_time -= 1
                logged_time = current_time
                if soak_time > 0:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, Current Temp: {current_temp:.2f}, Set Temp: {current_set_temp:.2f}, Soak Time: {soak_time//60}m {soak_time%60}s")
                elif stable_time > 0:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, Current Temp: {current_temp:.2f}, Set Temp: {current_set_temp:.2f}, Stability Time Left: {stable_time//60}m {stable_time%60}s")
                else:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, Current Temp: {current_temp:.2f}, Set Temp: {current_set_temp:.2f}")
        else:
            logging.error("Failed to retrieve temperature data after 3 attempts")
        #time.sleep(0.5)


def main():
    s = connect_tc()
    if s:
        #set_temp(s, get_temp(s))

        run_temp(s, 650, 5, 5)
        set_temp(s, 100)
        #print(get_temp(s))
    else:
        logging.error("Failed to connect to temperature controller")

if __name__ == "__main__":
    main()
