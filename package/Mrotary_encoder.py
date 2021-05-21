#!/usr/bin/env python3
'''
Pass the pins the clk/dt and button are connected to. Records the position of the button
both CW and CCW. Starts at 0 and increments by 1 or -1.

Returns two integers: (1) the position of the knob and (2) the state of the button, 0 or 1.

'''

import logging
import RPi.GPIO as GPIO

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
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.clkPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(self.dtPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    self.clkLastState = GPIO.input(self.clkPin)
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)
    GPIO.add_event_detect(self.button, GPIO.BOTH, callback=self._button_callback)
    self.logger.info('Rotary Encoder pins- clk:{0} data:{1} button:{2}'.format(self.clkPin, self.dtPin, self.button))

  def getdata(self):
    self.clkState = GPIO.input(self.clkPin)
    self.dtState = GPIO.input(self.dtPin)
    if self.clkState != self.clkLastState or self.buttonpressed:
      if self.clkState != self.clkLastState:
        if self.dtState != self.clkState:
          self.counter -= 0.5
        else:
          self.counter += 0.5
        self.clkLastState = self.clkState
      buttonstate = GPIO.input(self.button)
      self.buttonpressed = False
      if self._is_integer(self.counter):
        self.outgoing[self.og_counter] = self.counter
        self.outgoing[self.og_button] = buttonstate
        self.logger.debug(self.outgoing)
        return self.outgoing
  
  def _button_callback(self, channel):
    self.buttonpressed = True

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

if __name__ == "__main__":
  _loggers = []
  logging.basicConfig(level=logging.DEBUG) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.
  logging.info("GPIO version: {0}".format(GPIO.VERSION))
  main_logger = logging.getLogger(__name__)
  _loggers.append(main_logger)
  logger_rotenc = logging.getLogger('rotenc')
  logger_rotenc.setLevel(logging.INFO)
  _loggers.append(logger_rotenc)
  for logger in _loggers:
    main_logger.info('{0} is set at level: {1}'.format(logger, logger.getEffectiveLevel()))
  clkPin = 17              # Using BCM GPIO number for pins
  dtPin = 27
  button = 24
  data_keys = ['RotEncCi', 'RotEncBi']
  rotEnc1 = RotaryEncoder(clkPin, dtPin, button, *data_keys, logger_rotenc)
  
  try:
    while True:
      clicks = rotEnc1.getdata()
  except KeyboardInterrupt:
    logging.info("Pressed ctrl-C")
  finally:
    GPIO.cleanup()
    logging.info("GPIO cleaned up")

