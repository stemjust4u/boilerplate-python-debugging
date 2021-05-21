'''
Create dummy devices for testing

Data is simulated/created with random and numpy methods

'''

import logging, random
import numpy as np
from time import sleep, time, perf_counter_ns
from dataclasses import dataclass
from typing import List

@dataclass
class StepperMotor:
    pins: list       # Pins connected to ULN2003 IN1,2,3,4
    step: int        # Counter to keep track of motor step (0-4076 in halfstep mode)
    speed: list      # 0=fullstepCCW, 1=halfstepCCW, 2=stop, 3=halfstep CW, 4=fullstep CW
    coils: dict      # Arrays to specify HIGH pulses sent to coils.

@dataclass
class Machine:
    stepper: List[StepperMotor]

class Stepper:   # command comes from node-red GUI
    def __init__(self, *args, **kwargs):
        
        for key, value in kwargs.items():
            if key == 'logger':
                self.logger = kwargs[key]   #  Use logger passed as argument
            elif len(logging.getLogger().handlers) == 0:   # Root logger does not exist and no custom logger passed
                logging.basicConfig(level=logging.INFO)      # Create root logger
                self.logger = logging.getLogger(__name__)    # Create from root logger
            else:                                          # Root logger already exists and no custom logger passed
                self.logger = logging.getLogger(__name__)    # Create from root logger
        self.FULLREVOLUTION = 4076    # Steps per revolution
        motorpins = args
        motors = []
        for pinlist in motorpins:
            motors.append(StepperMotor(pinlist, 0, [0,0,0,0,0], {"Harr1":[0,1], "Farr1":[0,1], "arr2":[0,1], "arr3":[0,1], "HarrOUT":[0,1], "FarrOUT":[0,1]}))
        self.mach = Machine(motors)
        # Setup and initialize motor parameters
        #GPIO.setmode(GPIO.BCM)
        self.startstepping = []     # Flag sent from nodered dashboard to start stepping in increment mode
        self.targetstep = []        # When in mode1/increment a target step is calculated.
        self.reportsteps = [False,[]]  # Container to get the steps each motor is at for updating nodered dashboard
        self.rpmtime0 = [] # used for rpm calculation
        self.tloop = perf_counter_ns() # debugging tool
        self.rpmsteps0 = []
        self.rpm = []
        self.delay = 0   # Container to store loop delay
        self.timens = []  # monitor how long each motor loop takes (coil logic only)
        self.timems = [] # monitor how long each motor loop takes (coil logic + delay)
        self.outgoing = {}
        
        for i in range(len(self.mach.stepper)):          # Setup each stepper motor
            self.mach.stepper[i].speed[2] = [0,0,0,0]    # Speed 2 is hard coded as stop
            self.reportsteps[1].append(0)
            self.startstepping.append(False)  
            self.targetstep.append(291)         
            self.rpmtime0.append(perf_counter_ns())
            self.rpmsteps0.append(0)
            self.rpm.append(0)
            self.timens.append(perf_counter_ns())
            self.timems.append(perf_counter_ns())
            for rotation in range(2):        # Setup starting array for each rotation (CW,CCW) and H-half/F-full step
                self.mach.stepper[i].coils["Harr1"][rotation] = [0,0,1,1]
                self.mach.stepper[i].coils["Farr1"][rotation] = [0,0,1,1]
                self.mach.stepper[i].coils["arr2"][rotation] = [0,0,0,1]
                self.mach.stepper[i].coils["arr3"][rotation] = [0,0,1,0]
            for pin in self.mach.stepper[i].pins:        # Setup each pin in each stepper
                #GPIO.setup(pin,GPIO.OUT)
                self.logger.info("pin {0} Setup".format(pin))

    def step(self, incomingD):
        ''' LOOP THRU EACH STEPPER AND THE TWO ROTATIONS (CW/CCW) AND SEND COIL ARRAY (HIGH PULSES) '''
        self.command = incomingD
        self.delay = self.command["delay"][0]        # First delay is half step loop pause. Second value is add-on for full step.
        for i in range(len(self.mach.stepper)):   # Loop thru each stepper
            self.timens[i] = perf_counter_ns() # time counter for monitoring how long the loop takes
            stepspeed = self.command["speed"][i]         # stepspeed is a temporary variable for this loop
            if stepspeed > 2:
                rotation = 0 if self.command["inverse"][i] else 1
            elif stepspeed < 2:
                rotation = 1 if self.command["inverse"][i] else 0
                
            if stepspeed == 3 or stepspeed == 1:  # Half step calculation
                if rotation == 1:            # H is for half-step. Do array rotation (slicing) by 1 place to the right for CW
                    self.mach.stepper[i].coils["HarrOUT"][rotation] = self.mach.stepper[i].coils["Harr1"][rotation][-1:] + self.mach.stepper[i].coils["Harr1"][rotation][:-1]
                    self.mach.stepper[i].coils["Harr1"][rotation] = self.mach.stepper[i].coils["arr2"][rotation]
                    self.mach.stepper[i].coils["arr2"][rotation] = self.mach.stepper[i].coils["HarrOUT"][rotation]
                else:                        # Array rotation (slicing) 1 place to the left for CCW. And use arr3
                    self.mach.stepper[i].coils["HarrOUT"][rotation] = self.mach.stepper[i].coils["Harr1"][rotation][1:] + self.mach.stepper[i].coils["Harr1"][rotation][:1]
                    self.mach.stepper[i].coils["Harr1"][rotation] = self.mach.stepper[i].coils["arr3"][rotation]
                    self.mach.stepper[i].coils["arr3"][rotation] = self.mach.stepper[i].coils["HarrOUT"][rotation]
            if stepspeed == 4 or stepspeed == 0:  # Full step calculation          
                self.delay = self.command["delay"][0] + self.command["delay"][1] # Add extra delay for full step
                if rotation == 1:            # F is for full-step. Do array rotation (slicing) by 1 place to the right for CW
                    self.mach.stepper[i].coils["FarrOUT"][rotation] = self.mach.stepper[i].coils["Farr1"][rotation][-1:] + self.mach.stepper[i].coils["Farr1"][rotation][:-1]
                    self.mach.stepper[i].coils["Farr1"][rotation] = self.mach.stepper[i].coils["FarrOUT"][rotation]
                else:                        # Array rotation (slicing) 1 place to the left for CCW 
                    self.mach.stepper[i].coils["FarrOUT"][rotation] = self.mach.stepper[i].coils["Farr1"][rotation][1:] + self.mach.stepper[i].coils["Farr1"][rotation][:1]
                    self.mach.stepper[i].coils["Farr1"][rotation] = self.mach.stepper[i].coils["FarrOUT"][rotation]
            
            # Now that coil array updated set the 4 available speeds/direction. Half step CW & CCW. Full step CW & CCW.
            if not self.command["inverse"][i]: # Normal rotation pattern. speed 3/4=rot1(CW). speed 0/1=rot0 (CCW). 
                self.mach.stepper[i].speed[0] = self.mach.stepper[i].coils["FarrOUT"][0]
                self.mach.stepper[i].speed[1] = self.mach.stepper[i].coils["HarrOUT"][0]
                self.mach.stepper[i].speed[3] = self.mach.stepper[i].coils["HarrOUT"][1]
                self.mach.stepper[i].speed[4] = self.mach.stepper[i].coils["FarrOUT"][1]
            elif self.command["inverse"][i]:  # Inverse rotation pattern. speed 3/4=rot0(CCW). speed 0/1=rot1 (CW). 
                self.mach.stepper[i].speed[0] = self.mach.stepper[i].coils["FarrOUT"][1]
                self.mach.stepper[i].speed[1] = self.mach.stepper[i].coils["HarrOUT"][1]
                self.mach.stepper[i].speed[3] = self.mach.stepper[i].coils["HarrOUT"][0]
                self.mach.stepper[i].speed[4] = self.mach.stepper[i].coils["FarrOUT"][0]
            

            # If mode is 1 (incremental stepping) and startstep has been flagged from node-red gui then startstepping
            if self.command["mode"][i] == 1 and stepspeed != 2 and self.command["startstep"][i] == 1:
                self.startstepping[i] = True
                self.command["startstep"][i] = 0 # startstepping triggered and targetstep calculated. So turn off this if cond
                if stepspeed > 2: # moving CW 
                    if abs(self.mach.stepper[i].step) + self.command["step"][i] <= self.FULLREVOLUTION: # Set the target step based on node-red gui target and current step for that motor
                        self.targetstep[i] = abs(self.mach.stepper[i].step) + self.command["step"][i]
                    else:
                        self.targetstep[i] = self.FULLREVOLUTION
                else:      # moving CCW
                    self.targetstep[i] = self.mach.stepper[i].step - self.command["step"][i]
                    if self.targetstep[i] < (self.FULLREVOLUTION * -1):
                        self.targetstep[i] = (self.FULLREVOLUTION * -1)
                self.logger.debug("2:STRTSTP ON - Motor:{0} Mode:{1} startstep:{2} startstepping:{3} machStep:{4} targetstep:{5}".format(i, self.command["mode"][i], self.command["startstep"][i], self.startstepping[i], self.mach.stepper[i].step, self.targetstep[i]))
            
            # Mode set to 1 (incremental stepping) but haven't started stepping. Stop motor (stepspeed=2) and set the target step (based on node-red gui)
            # Will wait until startstep flag is sent from node-red GUI before starting motor
            if self.command["mode"][i] == 1 and not self.startstepping[i]:
                stepspeed = 2
                self.command["speed"][i] = 2
                self.logger.debug("1:MODE1      - Motor:{0} Mode:{1} startstep:{2} startstepping:{3} machStep:{4} targetstep:{5}".format(i, self.command["mode"][i], self.command["startstep"][i], self.startstepping[i], self.mach.stepper[i].step, self.targetstep[i]))
            
            # IN INCREMENT MODE1. Keep stepping until the target step is met. Then reset the startstepping/startstep(nodered) flags.
            elif self.command["mode"][i] == 1 and self.startstepping[i]:
                self.logger.debug("3:STEPPING   - Motor:{0} Mode:{1} startstep:{2} startstepping:{3} machStep:{4} targetstep:{5}".format(i, self.command["mode"][i], self.command["startstep"][i], self.startstepping[i], self.mach.stepper[i].step, self.targetstep[i]))
                if abs((abs(self.mach.stepper[i].step) - abs(self.targetstep[i]))) < 2: # if delta is less than 2 then target met. Can't use 0 since full step increments by 2
                    self.logger.debug("4:DONE-M1OFF - Motor:{0} Mode:{1} startstep:{2} startstepping:{3} machStep:{4} targetstep:{5}".format(i, self.command["mode"][i], self.command["startstep"][i], self.startstepping[i], self.mach.stepper[i].step, self.targetstep[i]))
                    self.startstepping[i] = False
                    #command["startstep"][i] = 0

            # SEND COIL ARRAY (HIGH PULSES) TO GPIO PINS AND UPDATE STEP COUNTER
            #GPIO.output(self.mach.stepper[i].pins, self.mach.stepper[i].speed[stepspeed]) # output the coil array (speed/direction) to the GPIO pins.
            self.logger.debug("Motor:{0} Steps:{1} Mode:{2} startstepping:{3} coils:{4}".format(i, self.mach.stepper[i].step, self.command["mode"][i], self.startstepping[i], self.mach.stepper[i].speed[stepspeed]))
            self.mach.stepper[i].step = self.stepupdate(stepspeed, self.mach.stepper[i].step)  # update the motor step based on direction and half vs full step
            
            # IF FULL REVOLUTION - reset the step counter
            if (abs(self.mach.stepper[i].step) > self.FULLREVOLUTION):  # If hit full revolution reset the step counter. If want to step past full revolution would need to later add a 'not startstepping'
                self.logger.debug("FULL REVOLUTION -- Motor:{0} Steps:{1} Mode:{2} startstepping:{3} coils:{4}".format(i, self.mach.stepper[i].step, self.command["mode"][i], self.startstepping[i], self.mach.stepper[i].speed[self.command["speed"][i]]))
                self.mach.stepper[i].step = 0
            
            # Timers to monitor how long the loops is taking
            self.timens[i] = perf_counter_ns() - self.timens[i]
            self.timems[i] = (self.timens[i]/1000000) + self.delay
        sleep(float(self.delay/1000))  # delay can be updated from node-red gui. Needs optimal setting for the motors.

    def getdata(self):
        ''' RETURN MOTOR DATA INCLUDING STEPS, RPMS, ETC '''
        for i in range(len(self.mach.stepper)):
            rpm = ((self.mach.stepper[i].step - self.rpmsteps0[i])/self.FULLREVOLUTION)/((perf_counter_ns() - self.rpmtime0[i])/60000000000)
            if rpm >= 0:
                self.rpm[i] = rpm
            self.rpmsteps0[i] = self.mach.stepper[i].step
            self.rpmtime0[i] = perf_counter_ns()
            self.outgoing['steps' + str(i) + 'i'] = self.mach.stepper[i].step
            self.outgoing['rpm'+ str(i) + 'f'] = self.rpm[i]
            self.outgoing['looptime'+ str(i) + 'f'] = self.timems[i]
            self.outgoing['speed'+ str(i) + 'i'] = self.command["speed"][i]
        self.outgoing['delayf'] = self.delay
        f0 = open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
        self.outgoing['cpufreq0i'] = int(int(f0.read()) / 1000)
        return self.outgoing

    def resetsteps(self):
        for i in range(len(self.mach.stepper)):
            self.mach.stepper[i].step = 0

    def stepupdate(self, spd, stp):
        ''' Will update the motor step counter based on full vs half speed and CW vs CCW. Details in Stepper Class'''
        if spd == 4:
            stp += 2
        elif spd ==3:
            stp += 1
        elif spd == 1:
            stp -= 1
        elif spd == 0:
            stp -= 2
        else:
            stp = stp
        return stp

class ServoKit:
    def __init__(self, address, channels):
        self.dummy = address
        self.dummy2 = channels

    def servo(self, angle):
        self.angle = angle
        
class RotaryEncoder:
    def __init__(self, clkPin, dtPin, button, key1='RotEncCi', key2='RotEncBi', logger=None):
        self.clkPin = clkPin
        self.dtPin = dtPin
        self.button = button
        self.outgoing = {}
        self.og_counter = key1
        self.og_button = key2
        if logger is not None:                         # Use logger passed as argument
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
            return self.adc    # Return dict with voltage for each channel: a0f, a1f, a2f etc

class mcp3008:
    ''' ADC using MCP3008 (SPI). Returns a list with voltage values '''

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
            return self.adc   # Return dict with voltage for each channel: a0f, a1f, a2f etc



if __name__ == "__main__":
    _loggers = []
    logging.basicConfig(level=logging.DEBUG) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
    main_logger = logging.getLogger(__name__)
    _loggers.append(main_logger)

    logger_stepper = logging.getLogger('stepper')
    logger_stepper.setLevel(logging.DEBUG)
    _loggers.append(logger_stepper)
    reportsteps = []
    incomingD={"delay":[0.8,1.0], "speed":[3,3], "mode":[0,0], "inverse":[False,False], "step":[2038, 2038], "startstep":[0,0]}
    data_keys = ['delayf', 'cpufreq0i', 'looptime0f', 'looptime1f', 'steps0i', 'steps1i', 'rpm0f', 'rpm1f', 'speed0i', 'speed1i']
    m1pins = [12, 16, 20, 21]
    m2pins = [19, 13, 6, 5]
    motor = Stepper(m1pins, m2pins, logger=logger_stepper)  # can enter 1 to 2 list of pins (up to 2 motors)

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
            volt_current_power = ina219A.getdata()
            logging.debug(volt_current_power)

            voltage = adc_ads1115.getdata()
            if voltage is not None:
                logging.debug(voltage)

            voltage = adc_mcp3008.getdata()
            if voltage is not None:
                logging.debug(voltage)

            clicks = rotEnc1.getdata()
            if clicks is not None:
                logging.debug(clicks)
            
            for x in range(20):
                motor.step(incomingD)
            outgoingD = motor.getdata()
            for key in outgoingD.keys():
                main_logger.debug(key)
            main_logger.debug(outgoingD)
            sleep(1)
    except KeyboardInterrupt:
        logging.info("Pressed ctrl-C")
    finally:
        logging.info("GPIO cleaned up")