import sys, json, logging, re
#import RPi.GPIO as GPIO
from time import sleep, perf_counter
import paho.mqtt.client as mqtt
from os import path
from pathlib import Path
from logging.handlers import RotatingFileHandler
from package import *

class pcolor:
    ''' Add color to print statements '''
    LBLUE = '\33[36m'   # Close to CYAN
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    DBLUE = '\33[34m'
    WOLB = '\33[46m'    # White On LightBlue
    LPURPLE = '\033[95m'
    PURPLE = '\33[35m'
    WOP = '\33[45m'     # White On Purple
    GREEN = '\033[92m'
    DGREEN = '\33[32m'
    WOG = '\33[42m'     # White On Green
    YELLOW = '\033[93m'
    YELLOW2 = '\33[33m'
    RED = '\033[91m'
    DRED = '\33[31m'
    WOR = '\33[41m'     # White On Red
    BOW = '\33[7m'      # Black On White
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    
class CustomFormatter(logging.Formatter):
    """ Custom logging format with color """

    grey = "\x1b[38;21m"
    green = "\x1b[32m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(levelname)s]: %(name)s - %(message)s"

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(log_dir, logger_type, logger_name=__name__, log_level=logging.INFO, mode=1):
    ''' Create basic or custom loggers with RotatingFileHandler '''
    global _loggers
    # logger_type = basic
    # logger_type = custom with log file options below
                # log_level and mode will determine output
                    #log_level, RFHmode|  logger.x() | output
                    #------------------|-------------|-----------
                    #      INFO, 1     |  info       | print
                    #      INFO, 2     |  info       | print+logfile
                    #      INFO, 3     |  info       | logfile
                    #      DEBUG,1     |  info+debug | print only
                    #      DEBUG,2     |  info+debug | print+logfile
                    #      DEBUG,3     |  info+debug | logfile

    if logger_type == 'basic':
        if len(logging.getLogger().handlers) == 0:       # Root logger does not already exist, will create it
            logging.basicConfig(level=log_level) # Create Root logger
            custom_logger = logging.getLogger(logger_name)    # Set logger to root logging
        else:
            custom_logger = logging.getLogger(logger_name)   # Root logger already exists so just linking logger to it
    else:
        if mode == 1:
            logfile_log_level = logging.CRITICAL
            console_log_level = log_level
        elif mode == 2:
            logfile_log_level = log_level
            console_log_level = log_level
        elif mode == 3:
            logfile_log_level = log_level
            console_log_level = logging.CRITICAL

        custom_logger = logging.getLogger(logger_name)
        custom_logger.propagate = False
        custom_logger.setLevel(log_level)
        log_file_format = logging.Formatter("[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(pathname)s:%(lineno)d")
        #log_console_format = logging.Formatter("[%(levelname)s]: %(message)s") # Using CustomFormatter Class

        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(CustomFormatter())

        log_file_handler = RotatingFileHandler('{}/debug.log'.format(log_dir), maxBytes=10**6, backupCount=5) # 1MB file
        log_file_handler.setLevel(logfile_log_level)
        log_file_handler.setFormatter(log_file_format)

        log_errors_file_handler = RotatingFileHandler('{}/error.log'.format(log_dir), maxBytes=10**6, backupCount=5)
        log_errors_file_handler.setLevel(logging.WARNING)
        log_errors_file_handler.setFormatter(log_file_format)

        custom_logger.addHandler(console_handler)
        custom_logger.addHandler(log_file_handler)
        custom_logger.addHandler(log_errors_file_handler)
    if custom_logger not in _loggers: _loggers.append(custom_logger)
    return custom_logger
                
def on_connect(client, userdata, flags, rc):
    """ on connect callback verifies a connection established and subscribe to TOPICs"""
    main_logger.info("attempting on_connect")
    if rc==0:
        mqtt_client.connected = True
        for topic in MQTT_SUB_TOPIC:
            client.subscribe(topic)
            main_logger.info("Subscribed to: {0}".format(topic))
        main_logger.info("Successful Connection: {0}".format(str(rc)))
    else:
        mqtt_client.failed_connection = True  # If rc != 0 then failed to connect. Set flag to stop mqtt loop
        main_logger.info("Unsuccessful Connection - Code {0}".format(str(rc)))

def on_message(client, userdata, msg):
    """on message callback will receive messages from the server/broker. Must be subscribed to the topic in on_connect"""
    global deviceD, MQTT_REGEX
    global mqtt_servoID, mqtt_servoAngle, mqtt_dummy1, mqtt_dummy2
    mqtt_logger.debug("Received: {0} with payload: {1}".format(msg.topic, str(msg.payload)))
    msgmatch = re.match(MQTT_REGEX, msg.topic)   # Check for match to subscribed topics
    if msgmatch:
        mqtt_payload = json.loads(str(msg.payload.decode("utf-8", "ignore"))) 
        mqtt_topic = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(mqtt_payload)] # breaks msg topic into groups - group/group1/group2
        if mqtt_topic[1] == 'servoZCMD':
            mqtt_servoID = int(mqtt_topic[2])
            mqtt_servoAngle = int(mqtt_payload)  # Set the servo angle from mqtt payload
        if mqtt_topic[2] == 'group2A':
            mqtt_dummy1 = mqtt_payload
        elif mqtt_topic[2] == 'group2B':
            mqtt_dummy2 = mqtt_payload
    # If Debugging will print the JSON incoming payload and unpack it
    if mqtt_logger.getEffectiveLevel() == 10:
        mqtt_logger.debug("Topic grp0:{0} grp1:{1} grp2:{2}".format(msgmatch.group(0), msgmatch.group(1), msgmatch.group(2)))
        mqtt_payload = json.loads(str(msg.payload.decode("utf-8", "ignore")))
        mqtt_logger.debug("Payload type:{0}".format(type(mqtt_payload)))
        if isinstance(mqtt_payload, (str, bool, int, float)):
            mqtt_logger.debug(mqtt_payload)
        elif isinstance(mqtt_payload, list):
            mqtt_logger.debug(mqtt_payload)
        elif isinstance(mqtt_payload, dict):
            for key, value in mqtt_payload.items():  
                mqtt_logger.debug("{0}:{1}".format(key, value))

def on_publish(client, userdata, mid):
    """on publish will send data to client"""
    mqtt_logger.debug("msg ID: " + str(mid)) 
    pass 

def on_disconnect(client, userdata,rc=0):
    main_logger.error("DisConnected result code "+str(rc))
    mqtt_client.loop_stop()

def mqtt_setup(IPaddress):
    global MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD, MQTT_SUB_TOPIC, MQTT_PUB_LVL1, MQTT_SUB_LVL1, MQTT_REGEX
    global mqtt_client
    home = str(Path.home())                       # Import mqtt and wifi info. Remove if hard coding in python script
    with open(path.join(home, "stem"),"r") as f:
        user_info = f.read().splitlines()
    MQTT_SERVER = IPaddress                    # Replace with IP address of device running mqtt server/broker
    MQTT_USER = user_info[0]                   # Replace with your mqtt user ID
    MQTT_PASSWORD = user_info[1]               # Replace with your mqtt password
    # Specific MQTT SUBSCRIBE/PUBLISH TOPICS created inside 'setup_device' function
    MQTT_SUB_TOPIC = []
    MQTT_SUB_LVL1 = 'nred2' + MQTT_CLIENT_ID
    MQTT_REGEX = MQTT_SUB_LVL1 + '/([^/]+)/([^/]+)' # 'nred2pi/+' would also work but would not return groups
                                              # () group capture. Useful for getting topic lvls in on_message
                                              # [^/] match a char except /. Needed to get topic lvl2, lvl3 groups
                                              # + will match one or more. Requiring at least 1 match forces a lvl1/lvl2/lvl3 topic structure
                                              # * could also be used for last group and then a lvl1/lvl2 topic would also be matched
    MQTT_PUB_LVL1 = 'pi2nred/'

    # MQTT STRUCTURE - TOPIC/PAYLOAD
    # TOPIC levels --> lvl1/lvl2/lvl3
    # PAYLOAD contains the data (JSON string represinting python/js object with key:value is best format
    #                            but can also be simple int, str, boolean)
    #
    # MQTT_SUBSCRIBE_TOPIC FORMAT
    # lvl1 = 'nred2' + MQTT_CLIENT -- From nodered to machine. machine can be generic or unique/specific
    # lvl2 = 'device function'     -- Example servoZCMD, stepperZCMD
    # lvl3 = free form             -- Example controls (stepper controls); 0,1,2 (specific servo)
    #
    # MQTT_PUBLISH_TOPIC FORMAT
    # lvl1 = 'pi2nred'|'esp2nred'  -- From machine to nodered. (generic machine)
    # lvl2 = 'device' sending data -- Device examples, adc, ina219, rotary encoder, stepper
    #        'deviceA'|'deviceB'      Device can be generic or specific. this is updated in 'create_device' functions
    #        'nredZCMD'               May also be machine sending command to nred to update dashboard
    # lvl3 = free form             -- May be specific machine (MQTT_CLIENT_ID) or general command
    #
    # MQTT PAYLOAD CONVERSIONS
    # Simple commands/data sent with integer, boolean, string, list payloads
    # Complex commands/data payloads sent with JSON format using python dict/js object notation (key:value)
    #  mach2nred
    #   PYTHON(publish)  -- Convert from python_object to JSON string/payload [json.dumps(python_object) --> JSON_msg.payload ]
    #   NODERED(mqtt_in) -- Convert from JSON string/payload to js_object     [JSON.parse(JSON_msg.payload) --> js_object     ] 
    #                       js_object named 'fields' to align with influxdb naming (values accessed with fields[key]=value or fields.key=value)
    #  nred2mach
    #   NODERED(mqtt_out)  -- mqtt_out: Keep node red data in js_object format (fields[key]=value)
    #   PYTHON(on_message) -- Convert JSON string payload to python_object    [python_object <-- json.loads(msg.payload.decode)]
    #
    # MSG PAYLOAD KEY:VALUE FORMAT  (script is demoMQTT.py, module is lib/Module.py)
    #  STEPS -- synchronize python dict keys with NodeRed js object keys using 'mqtt_payload_keys'
    #   1 - Define mqtt_payload_keys (key labels for python/js objects) in python script 'create_device' functions
    #       mqtt_payload_keys is then passed to the device module as an argument
    #   2 - Design device module so the 'outgoing' data will be a dictionary using the mqtt_payload_key names
    #   3 - Have Python script retrieve 'outgoing' data (dict) from device and publish using mqtt_payload_key names
    #   4 - NodeRed JSON.parse function will convert msg.payload ('outgoing') to js_object
    #        mqtt_payload_key names are used to create js_object (fields) keys
    #        fields/js_object items can be used in node red dashboard using fields.key (in nodered will be payload[0].key)
    #
    # NODE-RED BACKGROUND
    #  Topic/payload format tries to align with influxdb (TAGS/FIELDS) to make writing to database easy
    #  Topic levels are converted to TAGS inside NodeRed
    #  JSON string is used to construct js_object with FIELDS (fields[key]=value) 
    # The NodeRed msg.payload then becomes an array containing [FIELDS, TAGS]
    # Final NodeRed payload: fields[key]  data is accessed with msg.payload[0].key
    #                        tags(topic levels) are access with msg.payload[1].lvlx (lvl1, lvl2, lvl3)

def setup_device(device, lvl2, publvl3, data_keys):
    global printcolor, deviceD
    if deviceD.get(device) == None:
        deviceD[device] = {}
        deviceD[device]['data'] = {}
        deviceD[device]['lvl2'] = lvl2 # Sub/Pub lvl2 in topics. Does not have to be unique, can piggy-back on another device lvl2
        topic = f"{MQTT_SUB_LVL1}/{deviceD[device]['lvl2']}ZCMD/+"
        if topic not in MQTT_SUB_TOPIC:
            MQTT_SUB_TOPIC.append(topic)
            for key in data_keys:
                deviceD[device]['data'][key] = 0
        else:
            for key in data_keys:
                for item in deviceD:
                    if deviceD[item]['data'].get(key) != None:
                        main_logger.warning(f"**DUPLICATE WARNING {device} and {item} are both publishing {key} on {topic}")
                deviceD[device]['data'][key] = 0
        deviceD[device]['pubtopic'] = MQTT_PUB_LVL1 + lvl2 + '/' + publvl3
        deviceD[device]['send'] = False
        printcolor = not printcolor # change color of every other print statement
        if printcolor: 
            main_logger.info(f"{pcolor.LBLUE}{device} Subscribing to: {topic}{pcolor.ENDC}")
            main_logger.info(f"{pcolor.DBLUE}{device} Publishing  to: {deviceD[device]['pubtopic']}{pcolor.ENDC}")
            main_logger.info(f"JSON payload keys will be:{pcolor.WOLB}{*deviceD[device]['data'],}{pcolor.ENDC}")
        else:
            main_logger.info(f"{pcolor.PURPLE}{device} Subscribing to: {topic}{pcolor.ENDC}")
            main_logger.info(f"{pcolor.LPURPLE}{device} Publishing  to: {deviceD[device]['pubtopic']}{pcolor.ENDC}")
            main_logger.info(f"JSON payload keys will be:{pcolor.WOP}{*deviceD[device]['data'],}{pcolor.ENDC}")
    else:
        main_logger.error(f"Device {device} already in use. Device name should be unique")
        sys.exit(f"{pcolor.RED}Device {device} already in use. Device name should be unique{pcolor.ENDC}")

def button_callback(channel):
        global buttonpressed, buttonvalue
        buttonpressed = True
        buttonvalue = 1 # str(GPIO.input(jsbutton))

def main():
    global deviceD, printcolor      # Containers setup in 'create' functions and used for Publishing mqtt
    global MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, MQTT_CLIENT_ID, mqtt_client, MQTT_PUB_LVL1
    global _loggers, main_logger, mqtt_logger
    global buttonpressed, buttonvalue  # Joystick variables
    global mqtt_servoID                # Servo variables

    main_logger_level= logging.DEBUG # CRITICAL=logging off. DEBUG=get variables. INFO=status messages.
    main_logger_type = 'custom'       # 'basic' or 'custom' (with option for log files)
    RFHmode = 1 # log level and RFH mode will determine output for custom loggers
                # log_level and mode will determine output
                #log_level, RFHmode|  logger.x() | output
                #------------------|-------------|-----------
                #      INFO, 1     |  info       | print
                #      INFO, 2     |  info       | print+logfile
                #      INFO, 3     |  info       | logfile
                #      DEBUG,1     |  info+debug | print only
                #      DEBUG,2     |  info+debug | print+logfile
                #      DEBUG,3     |  info+debug | logfile
    
    _loggers = [] # container to keep track of loggers created
    main_logger = setup_logging(path.dirname(path.abspath(__file__)), main_logger_type, log_level=main_logger_level, mode=RFHmode)
    mqtt_logger = setup_logging(path.dirname(path.abspath(__file__)), 'custom', 'mqtt', log_level=logging.DEBUG, mode=1)
    
    # MQTT structure: lvl1 = from-to     (ie Pi-2-NodeRed shortened to pi2nred)
    #                 lvl2 = device type (ie servoZCMD, stepperZCMD, adc)
    #                 lvl3 = free form   (ie controls, servo IDs, etc)
    MQTT_CLIENT_ID = 'pi' # Can make ID unique if multiple Pi's could be running similar devices (ie servos, ADC's) 
                          # Node red will need to be linked to unique MQTT_CLIENT_ID
    mqtt_setup('10.0.0.115') # Pass IP address
    
    deviceD = {}  # Primary container for storing all devices, topics, and data
    printcolor = True
    #==== HARDWARE SETUP =====#
    rotaryEncoderSet = {}
    logger_rotenc = setup_logging(path.dirname(path.abspath(__file__)), 'custom', 'rotenc', log_level=logging.INFO, mode=2)

    device = 'rotEnc1'  # Device name should be unique, can not duplicate device ID
    lvl2 = 'rotencoder' # Topic lvl2 name can be a duplicate, meaning multiple devices publishing data on the same topic
    publvl3 = MQTT_CLIENT_ID + "" # Will be a tag in influxdb. Optional to modify it and describe experiment being ran
    data_keys = ['RotEnc1Ci', 'RotEnc1Bi'] # If topic lvl2 name repeats would likely want the data_keys to be unique
    clkPin, dtPin, button_rotenc = 17, 27, 24
    setup_device(device, lvl2, publvl3, data_keys)
    rotaryEncoderSet[device] =  RotaryEncoder(clkPin, dtPin, button_rotenc, *data_keys, logger_rotenc) #rotaryencoder.RotaryEncoder(clkPin, dtPin, button_rotenc, *data_keys, rotenc_logger)
    #------------#
    ina219Set = {}   # ina219 library has an internal logger named ina219. name it something different.
    logger_ina219 = setup_logging(path.dirname(path.abspath(__file__)), 'custom', 'ina219l', log_level=logging.INFO, mode=1)
    
    device = 'ina219A'  
    lvl2 = 'ina219A'  # Topic lvl2 name can be a duplicate, meaning multiple devices publishing data on the same topic
    publvl3 = MQTT_CLIENT_ID + "Test1" # Will be a tag in influxdb. Optional to modify it and describe experiment being ran
    data_keys = ['Vbusf', 'IbusAf', 'PowerWf'] # If topic lvl2 name repeats would likely want the data_keys to be unique
    setup_device(device, lvl2, publvl3, data_keys)
    ina219Set[device] = PiINA219(*data_keys, "auto", 0.4, 0x40, logger=logger_ina219) #  PiINA219(*data_keys, gainmode="auto", maxA=0.4, address=0x40, logger=ina219_logger) #piina219.PiINA219(*data_keys, gainmode="auto", maxA=0.4, address=0x40, logger=ina219_logger)
    #------------#
    adcSet = {}  # Can comment out any ADC type not being used
    adc_logger = setup_logging(path.dirname(path.abspath(__file__)), 'custom', 'adc', log_level=logging.INFO, mode=1)

    device = 'ads1115'
    lvl2 = 'ads1115' # Topic lvl2 name can be a duplicate, meaning multiple devices publishing data on the same topic
    publvl3 = MQTT_CLIENT_ID + "" # Will be a tag in influxdb. Optional to modify it and describe experiment being ran
    data_keys = ['a0f', 'a1f', 'etc'] # If topic lvl2 name repeats would likely want the data_keys to be unique
    setup_device(device, lvl2, publvl3, data_keys)
    adcSet[device] = ads1115(1, 0.003, 1, 1, 0x48, adc_logger) # numOfChannels, noiseThreshold (V), max interval, gain=1 (+/-4.1V readings), address
    
    device = 'mcp3008'
    lvl2 = 'mcp3008' # Topic lvl2 name can be a duplicate, meaning multiple devices publishing data on the same topic
    publvl3 = MQTT_CLIENT_ID + "" # Will be a tag in influxdb. Optional to modify it and describe experiment being ran
    data_keys = ['a0f', 'a1f', 'etc'] # If topic lvl2 name repeats would likely want the data_keys to be unique
    setup_device(device, lvl2, publvl3, data_keys)
    deviceD[device]['pubtopic2'] = f"{MQTT_SUB_LVL1}/nredZCMD/resetstepgauge"
    deviceD[device]['data2'] = "resetstepgauge"
    adcSet[device] = mcp3008(2, 5, 400, 1, 8, adc_logger) # numOfChannels, vref, noiseThreshold (raw ADC), maxInterval = 1sec, and ChipSelect GPIO pin (7 or 8)

    #Joystick button setup
    buttonpressed = False
    buttonvalue = 1
    jsbutton = 15
    #GPIO.setup(jsbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    #GPIO.add_event_detect(jsbutton, GPIO.BOTH, callback=button_callback)

    #------------#
    device = 'servoAngle'
    lvl2 = 'servo'
    publvl3 = MQTT_CLIENT_ID + ""
    data_keys = ['NA']             # Servo currently does not publish any data back to mqtt
    setup_device(device, lvl2, publvl3, data_keys)
    servoID, mqtt_servoID = 0, 0   # Initialize. Updated in mqtt on_message
    numservos = 16     # Number of servo channels to pass to ServoKit. Must be 8 or 16.
    mqtt_servoAngle = 90
    deviceD[device] = [90]*numservos   # Initialize at 90°
    i2caddr = 0x40
                      # Other arguments reference_clock_speed=25000000, frequency=50) 50Hz = 20ms period
    pca9685 = [ServoKit(address=i2caddr, channels=numservos)]*numservos
    #main_logger.info(('Servo PCA9685 Kit on address:{0} {1}'.format(i2caddr, pca9685)))

    main_logger.info("ALL DICTIONARIES")
    for device, item in deviceD.items():
        main_logger.info(device)
        if isinstance(item, dict):
            for key in item:
                main_logger.info("\t{0}:{1}".format(key, item[key]))
        else: main_logger.info("\t{0}".format(item))

    print("\n")
    for logger in _loggers:
        main_logger.info('{0} is set at level: {1}'.format(logger, logger.getEffectiveLevel()))

    #==== START/BIND MQTT FUNCTIONS ====#
    # Create a couple flags to handle a failed attempt at connecting. If user/password is wrong we want to stop the loop.
    mqtt.Client.connected = False             # Flag for initial connection (different than mqtt.Client.is_connected)
    mqtt.Client.failed_connection = False     # Flag for failed initial connection
    # Create our mqtt_client object and bind/link to our callback functions
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
    mqtt_client.on_connect = on_connect       # Bind on connect
    mqtt_client.on_disconnect = on_disconnect # Bind on disconnect
    mqtt_client.on_message = on_message       # Bind on message
    mqtt_client.on_publish = on_publish       # Bind on publish
    main_logger.info("Connecting to: {0}".format(MQTT_SERVER))
    mqtt_client.connect(MQTT_SERVER, 1883)    # Connect to mqtt broker. This is a blocking function. Script will stop while connecting.
    mqtt_client.loop_start()                  # Start monitoring loop as asynchronous. Starts a new thread and will process incoming/outgoing messages.
    # Monitor if we're in process of connecting or if the connection failed
    while not mqtt_client.connected and not mqtt_client.failed_connection:
        main_logger.info("Waiting")
        sleep(1)
    if mqtt_client.failed_connection:         # If connection failed then stop the loop and main program. Use the rc code to trouble shoot
        mqtt_client.loop_stop()
        sys.exit(f"{pcolor.RED}Connection failed. Check rc code to trouble shoot{pcolor.ENDC}")
    
    #==== MAIN LOOP ====================#
    # MQTT setup is successful. Initialize dictionaries and start the main loop.   
    t0_sec = perf_counter() # sec Counter for getting stepper data. Future feature - update interval in  node-red dashboard to link to perf_counter
    msginterval = 1       # Adjust interval to increase/decrease number of mqtt updates.
    outgoingD = {}
    try:
        while True:
            servoID = mqtt_servoID                                      # Servo commands coming from mqtt
            deviceD['servoAngle'][servoID] = mqtt_servoAngle            # But could change data source from something other than mqtt
            pca9685[servoID].servo(deviceD['servoAngle'][mqtt_servoID]) # Set the servo angle
            if (perf_counter() - t0_sec) > msginterval: # Get data on a time interval
                for device, ina219 in ina219Set.items():
                    deviceD[device]['data'] = ina219.getdata()
                    main_logger.debug("{} {}".format(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data'])))
                    #mqtt_client.publish(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data']))  # publish voltage values
                for device, adc in adcSet.items():
                    deviceD[device]['data'] = adc.getdata() # Get the readings from each adc
                    if deviceD[device]['data'] is not None:
                        main_logger.debug("{} {}".format(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data'])))
                        #mqtt_client.publish(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data']))
                    # For joystick with button
                    if buttonpressed or deviceD[device]['data'] is not None:
                        if deviceD[device]['data'] is not None:
                            outgoingD = deviceD[device]['data']
                        outgoingD['buttoni'] = buttonvalue
                        #mqtt_client.publish(deviceD[device]['pubtopic'], json.dumps(outgoingD))       # publish voltage values
                        buttonpressed = False
                        main_logger.debug(outgoingD)
                t0_sec = perf_counter()
            for device, rotenc in rotaryEncoderSet.items():
                deviceD[device]['data'] = rotenc.getdata()
                if deviceD[device]['data'] is not None:
                    main_logger.debug("{} {}".format(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data'])))
                    #mqtt_client.publish(deviceD[device]['pubtopic'], json.dumps(deviceD[device]['data']))
            sleep(1)
    except KeyboardInterrupt:
        main_logger.info(f"{pcolor.WARNING}Exit with ctrl-C{pcolor.ENDC}")
    finally:
        #GPIO.cleanup()
        main_logger.info(f"{pcolor.CYAN}GPIO cleaned up{pcolor.ENDC}")

if __name__ == "__main__":
    main()