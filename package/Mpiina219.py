#!/usr/bin/env python3

'''
Board 0: Address = 0x40 Offset = binary 00000 (no jumpers required)
Board 1: Address = 0x41 Offset = binary 00001 (bridge A0)
Board 2: Address = 0x44 Offset = binary 00100 (bridge A1)
Board 3: Address = 0x45 Offset = binary 00101 (bridge A0 & A1)
To check address
$ sudo i2cdetect -y 1

Can be put in low power mode
ina.sleep()
time.sleep(60)
ina.wake()

ina.reset()               # Reset the INA219 to its default configuration.
ina.is_conversion_ready() # check if conversion was done before reading the next measurement results.

#Debugging mode
ina = INA219(SHUNT_OHMS, log_level=logging.INFO) # See calibration calculation results and automatic gain increases
ina = INA219(SHUNT_OHMS, log_level=logging.DEBUG)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

RANGE*32V: Range zero to 32 volts (default)
RANGE*16V: Range zero to 16 volts

GAIN*AUTO: Automatically calculate the gain (default)
GAIN_1_40MV: Maximum shunt voltage 40mV
GAIN*2_80MV: Maximum shunt voltage 80mV

bus*adc: The bus ADC resolution (9, 10, 11, or 12-bit)
ADC*12BIT: 12 bit, conversion time 532us (default)
ADC*11BIT: 11 bit, conversion time 276us.
ADC*10BIT: 10 bit, conversion time 148us.
ADC*9BIT: 9 bit, conversion time 84us.
or
shunt*adc: The shunt ADC resolution (9, 10, 11, or 12-bit)
ADC*2SAMP: 2 samples at 12 bit, conversion time 1.06ms.
ADC*4SAMP: 4 samples at 12 bit, conversion time 2.13ms.
ADC*8SAMP: 8 samples at 12 bit, conversion time 4.26ms.
ADC*16SAMP: 16 samples at 12 bit, conversion time 8.51ms
ADC*32SAMP: 32 samples at 12 bit, conversion time 17.02ms.
ADC*64SAMP: 64 samples at 12 bit, conversion time 34.05ms.
ADC*128SAMP: 128 samples at 12 bit, conversion time 68.10ms.

'''

from ina219 import INA219
from ina219 import DeviceRangeError
import time, logging
from time import perf_counter, perf_counter_ns

class PiINA219:

    def __init__(self, voltkey='Vbusf', currentkey='IbusAf', powerkey='PowerWf', gainmode="auto", maxA = 0.4, address=0x40, logger=None): 
        self.SHUNT_OHMS = 0.1
        self.voltkey = voltkey
        self.currentkey = currentkey
        self.powerkey = powerkey
        self.address = address
        if logger is not None:                        # Use logger passed as argument
            self.logger = logger
        elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)      # Create root logger
            self.logger = logging.getLogger(__name__)    # Create from root logger
        else:                                          # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger        
        self.ina219 = INA219(self.SHUNT_OHMS, maxA, address=self.address)  # can pass log_level=log_level
        self.outgoing = {}
        if gainmode == "auto":      # AUTO GAIN, HIGH RESOLUTION - Lower precision above max amps specified
            self.ina219.configure(self.ina219.RANGE_16V)
        elif gainmode == "manual":  # MANUAL GAIN, HIGH RESOLUTION - Max amps is 400mA
            self.ina219.configure(self.ina219.RANGE_16V, self.ina219.GAIN_1_40MV)
        self.logger.info('ina219 at {0} setup with gain mode:{1} max Amps:{2}'.format(address, gainmode, maxA))
        self.logger.info(self.ina219)

    def getdata(self):
        self.outgoing[self.voltkey] =  self.ina219.voltage()
        try:
            self.outgoing[self.currentkey] = float("{:.3f}".format(self.ina219.current()/1000))
            self.outgoing[self.powerkey] = float("{:.2f}".format(self.ina219.power()/1000))
            #Vshunt = self.ina219.shunt_voltage()
        except DeviceRangeError as e:
            self.logger.info("Current overflow")
        self.logger.debug('{0}, {1}, {2}'.format(self.address, self.outgoing.keys(), self.outgoing.values()))
        return self.outgoing

    def sleep(self):
        self.ina219.sleep()

    def wake(self):
        self.ina219.wake()

    def reset(self):
        self.ina219.reset()

if __name__ == "__main__":
    from logging.handlers import RotatingFileHandler
    from os import path

    def setup_logging(log_dir, log_level=logging.INFO, mode=1):
        # Create loggers
        # INFO + mode 1  = info           print only
        # INFO + mode 2  = info           print+logfile output
        # DEBUG + mode 1 = info and debug print only
        # DEBUG + mode 2 = info and debug print+logfile output

        if mode == 1:
            logfile_log_level = logging.CRITICAL
        elif mode == 2:
            logfile_log_level = logging.DEBUG

        main_logger = logging.getLogger(__name__)
        main_logger.setLevel(log_level)
        log_file_format = logging.Formatter("[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(pathname)s:%(lineno)d")
        log_console_format = logging.Formatter("[%(levelname)s]: %(message)s")
 
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(log_console_format)

        log_file_handler = RotatingFileHandler('{}/debug.log'.format(log_dir), maxBytes=10**6, backupCount=5) # 1MB file
        log_file_handler.setLevel(logfile_log_level)
        log_file_handler.setFormatter(log_file_format)

        log_errors_file_handler = RotatingFileHandler('{}/error.log'.format(log_dir), maxBytes=10**6, backupCount=5)
        log_errors_file_handler.setLevel(logging.WARNING)
        log_errors_file_handler.setFormatter(log_file_format)

        main_logger.addHandler(console_handler)
        main_logger.addHandler(log_file_handler)
        main_logger.addHandler(log_errors_file_handler)
        return main_logger
    
    main_log_level= logging.DEBUG
    #logging.basicConfig(level=main_log_level) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
    main_logger = setup_logging(path.dirname(path.abspath(__file__)), main_log_level, 2)
    data_keys = ['Vbusf', 'IbusAf', 'PowerWf']
    ina219A = PiINA219(*data_keys, "auto", 0.4, 0x40, logger=main_logger)
    ina219B = PiINA219(*data_keys, "auto", 0.4, 0x41, logger=main_logger)
    #while True:
    for i in range(5):
        t0 = perf_counter_ns()
        reading = ina219A.getdata()
        tdelta = perf_counter_ns() - t0
        time.sleep(1)
    ina219A.sleep()
    for i in range(5):
        t0 = perf_counter_ns()
        reading = ina219A.getdata()
        tdelta = perf_counter_ns() - t0
        time.sleep(1)