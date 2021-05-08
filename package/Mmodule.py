import logging, random
import numpy as np
from time import sleep
class RotaryEncoder:
    def __init__(self, clkPin, dtPin, button, key1='RotEncCi', key2='RotEncBi', mlogger=None):
        self.clkPin = clkPin
        self.dtPin = dtPin
        self.button = button
        self.outgoing = {}
        self.og_counter = key1
        self.og_button = key2
        if mlogger is not None:                        # Use logger passed as argument
            self.logger = mlogger
        elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)      # Create root logger
            self.logger = logging.getLogger(__name__)    # Create from root logger
        else:                                          # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger
        self.counter = 0
        self.clkUpdate = True
        self.buttonpressed = False
        self.logger.info('Rotary Encoder pins- clk:{0} data:{1} button:{2}'.format(self.clkPin, self.dtPin, self.button))
        self.testcounter = np.arange(-10, 10, 0.5).tolist()
        self.testbutton = [0,0,1]

    def getdata(self):
        self.counter = random.choice(self.testcounter)
        buttonstate = random.choice(self.testbutton)
        self.logger.debug("Rotenc counter: {0} Button: {1}".format(self.counter, buttonstate))
        if self._is_integer(self.counter):
            self.outgoing[self.og_counter] = self.counter
            self.outgoing[self.og_button] = buttonstate
            self.logger.debug(self.outgoing)
            return self.outgoing


    def _is_integer(self, n):
        if n == None:
            return False
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    ''' alternative integer check
    def is_integer_num(n):
        if isinstance(n, int):
            return True
        if isinstance(n, float):
            return n.is_integer()
        return False
    '''

class PiINA219:

    def __init__(self, voltkey='Vbusf', currentkey='IbusAf', powerkey='PowerWf', gainmode="auto", maxA = 0.4, address=0x40, mlogger=None): 
        self.SHUNT_OHMS = 0.1
        self.voltkey = voltkey
        self.currentkey = currentkey
        self.powerkey = powerkey
        self.address = address
        if mlogger is not None:                        # Use logger passed as argument
            self.logger = mlogger
        elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)      # Create root logger
            self.logger = logging.getLogger(__name__)    # Create from root logger
        else:                                          # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger        
        #self.ina219 = INA219(self.SHUNT_OHMS, maxA, address=self.address)  # can pass log_level=log_level
        self.outgoing = {}
        #if gainmode == "auto":      # AUTO GAIN, HIGH RESOLUTION - Lower precision above max amps specified
            #self.ina219.configure(self.ina219.RANGE_16V)
        #elif gainmode == "manual":  # MANUAL GAIN, HIGH RESOLUTION - Max amps is 400mA
            #self.ina219.configure(self.ina219.RANGE_16V, self.ina219.GAIN_1_40MV)
        self.logger.info('ina219 at {0} setup with gain mode:{1} max Amps:{2}'.format(address, gainmode, maxA))
        #self.logger.info(self.ina219)

    def getdata(self):
        self.outgoing[self.voltkey] =  random.uniform(0, 5)
        self.outgoing[self.currentkey] = random.uniform(0, 1)
        self.outgoing[self.powerkey] = self.outgoing[self.voltkey] * self.outgoing[self.currentkey]
        self.logger.debug('{0}, {1}, {2}'.format(self.address, self.outgoing.keys(), self.outgoing.values()))
        return self.outgoing

if __name__ == "__main__":
    _loggers = []
    logging.basicConfig(level=logging.DEBUG) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
    main_logger = logging.getLogger(__name__)
    _loggers.append(main_logger)

    logger_rotenc = logging.getLogger('rotenc')
    logger_rotenc.setLevel(logging.INFO)
    _loggers.append(logger_rotenc)
    clkPin = 17              # Using BCM GPIO number for pins
    dtPin = 27
    button = 24
    data_keys = ['RotEncCi', 'RotEncBi']
    rotEnc1 = RotaryEncoder(clkPin, dtPin, button, *data_keys, logger_rotenc)
  
    logger_ina219 = logging.getLogger('rotenc')
    logger_ina219.setLevel(logging.DEBUG)
    _loggers.append(logger_ina219)
    data_keys = ['Vbusf', 'IbusAf', 'PowerWf']
    ina219A = PiINA219(*data_keys, "auto", 0.4, 0x40, mlogger=main_logger)
    ina219B = PiINA219(*data_keys, "auto", 0.4, 0x41, mlogger=main_logger)

    for logger in _loggers:
        main_logger.info('{0} is set at level: {1}'.format(logger, logger.getEffectiveLevel()))
    try:
        while 1:
            reading = ina219A.getdata()
            logging.info(reading)
            clicks = rotEnc1.getdata()
            if clicks is not None:
                logging.info(clicks)
            sleep(1)
    except KeyboardInterrupt:
        logging.info("Pressed ctrl-C")
    finally:
        logging.info("GPIO cleaned up")