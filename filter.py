import serial
import serial.tools.list_ports_windows
import numpy as np
import warnings
from typing import Optional, Tuple, Any
from collections.abc import Callable

def write_and_read(ser:serial.Serial, input_str:str, startsWith:str, eol_r:str, eol_w:str, cast_func:Callable) -> Any:
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(startsWith.encode('utf-8')+input_str.encode('utf-8') + eol_w.encode('utf-8'))
    ser.flush()
    data = ser.read_until(eol_r.encode('utf-8'))
    data = data.decode('utf-8')
    assert data.startswith(startsWith), f"Device returned unexpected response: {data}"
    if data.find(startsWith) + 1 == data.find(eol_r):
        return None
    else: 
        return cast_func(data[data.find(startsWith) + 1:data.find(eol_r)])

def connect(supress_output:bool = False, timeout:np.floating=0.1, **kwargs) -> Optional[serial.Serial]:
    ports = serial.tools.list_ports_windows.comports()
    for port in ports:
        if not supress_output:
            print(f"Scanning on {port.device}...")
        ser = serial.Serial(port.device, 9600, timeout=timeout, **kwargs)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(b'V,')
        ser.flush()
        data = ser.read_until(b' ')
        if data.decode('utf-8').startswith('V2'):
            return ser
        ser.close()
    print("No optical filter found.")

def scan(ser:serial.Serial, start:int, end:int, stay:np.floating, span:int, supress_output:bool = False, timeout:np.floating=5) -> Tuple[int, int, int]:
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    _stay = int(np.round(stay * 10))
    if start < 1510 or start > 1589:
        raise ValueError(f"The start wavelength has to be between 1510 and 1589, got {start}.")
    elif end < 1510 or end > 1589:
        raise ValueError(f"The end wavelength has to be between 1510 and 1589, got {end}.")
    elif _stay < 1 or _stay > 300:
        raise ValueError(f"The stay time has to be between 0.1 and 30.0, got {stay}.")
    elif span < 1 or span > 30:
        raise ValueError(f"The stay span has to be between 1 and 30, got {span}.")
    
    start_prev = write_and_read(ser, str(start).zfill(4), 'L', ' ', ',', int)
    end_prev = write_and_read(ser, str(end).zfill(4), 'H', ' ', ',', int)
    stay_prev = write_and_read(ser, str(_stay).zfill(4), 'T', ' ', ',', int)

    
    try:
        ser.write(('S'+str(span).zfill(4)+',').encode('utf-8'))
        ser.flush()
        while True:
            data = b''
            while data == b'':
                data = ser.read_until(b' ')
            data = data.decode('utf-8')
            assert data.startswith('S'), f"Device returned unexpected response: {data}"
            if data.find('S') + 1 == data.find(' ') or supress_output: continue
            else: print(f"Scanning wavelength {data[data.find('S') + 1 : data.find(' ')]}", end='\r')
    except AssertionError as e:
        if not data.startswith('o'): raise e

    return start_prev, end_prev, stay_prev

def set_channel(ser:serial.Serial, wl:np.floating, suppress_output:bool = False) -> int:
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    wl_int = int(np.round(wl))
    wl_fl = int(np.round((wl - wl_int) / 0.2))
    if wl_int < 1510 or wl_int > 1589:
        raise ValueError(f"The wavelength has to be between 1510 and 1589, got {wl}.")
    try:
        write_and_read(ser, str(wl_int).zfill(4), 'C', ' ', ',', None)
    except:
        return -1
    if not suppress_output and wl - (wl_int + wl_fl * 0.2) > 1e-6:
            warnings.warn(f"{wl} not achieveable, setting to closest wavelength {wl_int + wl_fl * 0.2}")
    if wl_fl == 0: return 0
    else:
        if wl_fl < 0:
            try: 
                write_and_read(ser, str(-wl_fl).zfill(4), 'D', ' ', ',', None)
            except:
                return -1
        else:
            try:
                write_and_read(ser, str(wl_fl).zfill(4), 'I', ' ', ',', None)
            except:
                return -1
        return 0