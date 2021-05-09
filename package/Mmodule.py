import logging, random
import numpy as np
from time import sleep, time
class RotaryEncoder:
    def __init__(self, clkPin, dtPin, button, key1='RotEncCi', key2='RotEncBi', logger=None):
        self.clkPin = clkPin
        self.dtPin = dtPin
        self.button = button
        self.outgoing = {}
        self.og_counter = key1
        self.og_button = key2
        if logger is not None:                        # Use logger passed as argument
            self.logger = logger
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
        #self.ina219 = INA219(self.SHUNT_OHMS, maxA, address=self.address)  # can pass log_level=log_level
        self.outgoing = {}
        #if gainmode == "auto":      # AUTO GAIN, HIGH RESOLUTION - Lower precision above max amps specified
            #self.ina219.configure(self.ina219.RANGE_16V)
        #elif gainmode == "manual":  # MANUAL GAIN, HIGH RESOLUTION - Max amps is 400mA
            #self.ina219.configure(self.ina219.RANGE_16V, self.ina219.GAIN_1_40MV)
        self.logger.info('ina219 using I2C at address {0} setup with gain mode:{1} max Amps:{2}'.format(address, gainmode, maxA))
        #self.logger.info(self.ina219)

    def getdata(self):
        self.outgoing[self.voltkey] =  float("%.2f"%random.uniform(0, 5))
        self.outgoing[self.currentkey] = float("%.2f"%random.uniform(0, 1))
        self.outgoing[self.powerkey] = float("%.2f"%(self.outgoing[self.voltkey] * self.outgoing[self.currentkey]))
        self.logger.debug('{0}, {1}, {2}'.format(self.address, self.outgoing.keys(), self.outgoing.values()))
        return self.outgoing

class ads1115:
    ''' ADC using ADS1115 (I2C). Returns a list with voltage values '''
    
    def __init__(self, numOfChannels=1, noiseThreshold=0.001, maxInterval=1, usergain=1, useraddress=0x48, logger=None):
        ''' Create I2C bus and initialize lists '''
        
        if logger is not None:                        # Use logger passed as argument
            self.logger = logger
        elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)      # Create root logger
            self.logger = logging.getLogger(__name__)    # Create from root logger
        else:                                          # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger
        self.logger.info("ADS1115 using I2C at address {0}".format(str(useraddress)))
        self.numOfChannels = numOfChannels
        self.noiseThreshold = noiseThreshold
        self.numOfSamples = 10        # Number of samples to average
        self.maxInterval = maxInterval  # interval in seconds to check for update
        self.time0 = time()   # time 0
        # Initialize lists
        self.sensorAve = [x for x in range(self.numOfChannels)]
        self.sensorLastRead = [x for x in range(self.numOfChannels)]
        self.adcValue = [x for x in range(self.numOfChannels)]
        self.adc = {}
        self.sensor = [[x for x in range(0, self.numOfSamples)] for x in range(0, self.numOfChannels)]
        self.sensorChanged = False
        self.timelimit = False

    def getdata(self):
        ''' If adc is above noise threshold or time limit exceeded will return voltage of each channel '''
        
        if time() - self.time0 > self.maxInterval:
            timelimit = True
        for x in range(self.numOfChannels):
            self.sensorAve[x] = float("%.2f"%random.uniform(0, 5))  # sum(self.sensor[x])/len(self.sensor[x])
            sensorChanged = True
            self.adc['a' + str(x) + 'f'] = self.sensorAve[x]
            self.sensorLastRead[x] = self.sensorAve[x]
            self.logger.debug('changed: {0} chan: {1} value: {2:1.3f} previously: {3:1.3f}'.format(sensorChanged, x, self.sensorAve[x], self.sensorLastRead[x]))
        if sensorChanged or timelimit:
            self.time0 = time()
            self.sensorChanged = False
            self.timelimit = False
            return self.adc

class mcp3008:
    ''' ADC using MCP3008 (SPI). Returns a list with voltge values '''

    def __init__(self, numOfChannels, vref, noiseThreshold=350, maxInterval=1, cs=8, logger=None):
        ''' Create spi connection and initialize lists '''
        
        if logger is not None:                        # Use logger passed as argument
            self.logger = logger
        elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
            logging.basicConfig(level=logging.INFO)      # Create root logger
            self.logger = logging.getLogger(__name__)    # Create from root logger
        else:                                          # Root logger already exists and no custom logger passed
            self.logger = logging.getLogger(__name__)    # Create from root logger
        self.vref = vref
        self.logger.info("MCP3008 using SPI ")
        self.numOfChannels = numOfChannels
        self.noiseThreshold = noiseThreshold
        self.numOfSamples = 10             # Number of samples to average
        self.maxInterval = maxInterval  # interval in seconds to check for update
        self.time0 = time()   # time 0
        # Initialize lists
        self.sensorAve = [x for x in range(self.numOfChannels)]
        self.sensorLastRead = [x for x in range(self.numOfChannels)]
        self.adcValue = [x for x in range(self.numOfChannels)]
        self.sensor = [[x for x in range(0, self.numOfSamples)] for x in range(0, self.numOfChannels)]
        self.sensorChanged = False
        self.timelimit = False
        self.adc = {}   # Container for sending final data
    
    def valmap(self, value, istart, istop, ostart, ostop):
        ''' Used to convert from raw ADC to voltage '''

        return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

    def getdata(self):
        ''' If adc is above noise threshold or time limit exceeded will return voltage of each channel '''
        
        if time() - self.time0 > self.maxInterval:
            self.timelimit = True
        for x in range(self.numOfChannels):
            self.sensorChanged = True
            self.adc['a' + str(x) + 'f'] = float("%.2f"%random.uniform(0, 5)) # self.adcValue[x]
            self.logger.debug('{0}'.format(self.adc))
        if self.sensorChanged or self.timelimit:
            self.time0 = time()
            self.sensorChanged = False
            self.timelimit = False
            return self.adc

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
  
    logger_ina219 = logging.getLogger('ina219')
    logger_ina219.setLevel(logging.INFO)
    _loggers.append(logger_ina219)
    data_keys = ['Vbusf', 'IbusAf', 'PowerWf']
    ina219A = PiINA219(*data_keys, "auto", 0.4, 0x40, logger=logger_ina219)
    ina219B = PiINA219(*data_keys, "auto", 0.4, 0x41, logger=logger_ina219)

    logger_ads1115 = logging.getLogger('ads1115')
    logger_ads1115.setLevel(logging.INFO)
    _loggers.append(logger_ads1115)
    adc_ads1115 = ads1115(2, 0.001, 1, 1, 0x48, logger=logger_ads1115)

    logger_mcp3008 = logging.getLogger('mcp3008')
    logger_mcp3008.setLevel(logging.DEBUG)
    _loggers.append(logger_mcp3008)
    adc_mcp3008 = mcp3008(2, 5, 400, 1, 8, logger=logger_mcp3008) # numOfChannels, vref, noiseThreshold, max time interval, chip select

    for logger in _loggers:
        main_logger.info('{0} is set at level: {1}'.format(logger, logger.getEffectiveLevel()))
    try:
        while 1:
            reading = ina219A.getdata()
            logging.debug(reading)

            voltage = adc_ads1115.getdata()
            if voltage is not None:
                logging.debug(voltage)

            voltage = adc_mcp3008.getdata()
            if voltage is not None:
                logging.debug(voltage)

            clicks = rotEnc1.getdata()
            if clicks is not None:
                logging.debug(clicks)
            
            sleep(1)
    except KeyboardInterrupt:
        logging.info("Pressed ctrl-C")
    finally:
        logging.info("GPIO cleaned up")