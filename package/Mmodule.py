import time, logging
from time import perf_counter, perf_counter_ns
import RPi.GPIO as GPIO

class device:

    def __init__(self, key1='Vf', key2='If', address=0x40, mlogger=None): 
        self.key1 = key1
        self.key2 = key2
        self.address = address
        if mlogger is not None:         # Use logger passed as argument
            self.logger = mlogger
        elif len(logging.getLogger().handlers) == 0:     # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)  # Create root logger
            self.logger = logging.getLogger(__name__)# Create from root logger
        else:                                            # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger       
        self.logger.info(f'device at {address} setup')
        self.logger.info(self.ina219)

    def read(self):
        self.outgoing[self.key1] =  self.ina219.voltage()
        try:
            self.outgoing[self.key2] = float("{:.2f}".format(self.ina219.current()))
        except DeviceRangeError as e:
            self.logger.info("Current overflow")
        self.logger.debug('{0}, {1}, {2}'.format(self.address, self.outgoing.keys(), self.outgoing.values()))
        return self.outgoing

    def cleanupGPIO(self):
        GPIO.cleanup()

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

        exp_file_handler = RotatingFileHandler('{}/exp_debug.log'.format(log_dir), maxBytes=10**6, backupCount=5) # 1MB file
        exp_file_handler.setLevel(logfile_log_level)
        exp_file_handler.setFormatter(log_file_format)

        exp_errors_file_handler = RotatingFileHandler('{}/exp_error.log'.format(log_dir), maxBytes=10**6, backupCount=5)
        exp_errors_file_handler.setLevel(logging.WARNING)
        exp_errors_file_handler.setFormatter(log_file_format)

        main_logger.addHandler(console_handler)
        main_logger.addHandler(exp_file_handler)
        main_logger.addHandler(exp_errors_file_handler)
        return main_logger
    
    main_log_level= logging.DEBUG
    #logging.basicConfig(level=main_log_level) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
    main_logger = setup_logging(path.dirname(path.abspath(__file__)), main_log_level, 2)
    payload_keys = ['Vbusf', 'IbusAf', 'PowerWf']
    ina219A = PiINA219(*payload_keys, "auto", 0.4, 0x40, mlogger=main_logger, mlog_level=main_log_level)
    ina219B = PiINA219(*payload_keys, "auto", 0.4, 0x41, mlogger=main_logger, mlog_level=main_log_level)
    #while True:
    for i in range(5):
        t0 = perf_counter_ns()
        reading = ina219A.read()
        tdelta = perf_counter_ns() - t0
        #logging.info('{0} {1}'.format(reading.keys(), reading.values()))
        time.sleep(1)
    ina219A.sleep()
    for i in range(5):
        t0 = perf_counter_ns()
        reading = ina219A.read()
        tdelta = perf_counter_ns() - t0
        #logging.info('{0} {1}'.format(reading.keys(), reading.values()))
        time.sleep(1)