from os import path
from pathlib import Path
# Initialize
logDir = path.dirname(__file__)
iFile = "input.csv"
oFile = "output.csv"
Path(path.join(logDir, oFile)).touch(exist_ok = True)


'''
3 methods to read/write a simple file
    1         2          3
f.write() json.dump pickle.dump
f.read()  json.load pickle.load

to read/write a csv file
import csv

to read/write excel type data
python3.7 -m pip install pandas
import pandas
'''

f = open("log.py", "r")
f.read()
f.readline().rstrip("\n")
f.close()

import csv
csvfile = "test.csv"
'''
device,measurement,value
pi,voltage,1.5
esp32,current,0.6
'''
with open(csvfile) as f:
    csv_reader = csv.reader(f, delimiter=',')   # example with 3 comma delimited fields
    line = 0
    for row in csv_reader:
        if line == 0:
            print(f'Cols names are {", ".join(row)}')
            line += 1
        else:
            print(f'\t{row[0]} {row[1]} {row[2]}')
            line += 1
    print(f'Read {line} lines.')

csvfile = "test.csv"
with open(csvfile, mode='w') as f:
    csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["device", "measurement", "value"])
    csv_writer.writerow(["pi", "voltage", 1.5])
    csv_writer.writerow(["esp32", "current", 0.6])
    csv_writer.writerow(["esp32", "voltage", 1.6])

with open(csvfile) as f:
    csv_reader = csv.DictReader(f, delimiter=',', quotechar='"', escapechar=None)
    line_num = 0
    print(*csv_reader.fieldnames)  # First line used as keys. Can unpack list and print them
    for row in csv_reader:
        if line_num == 0:
            print(f'Columns {", ".join(row)}')
        print(f'\t{row["device"]}\t{row["measurement"]}\t\t{row["value"]}')
        line_num += 1
    print(f'file had {line_num} rows of data')

csvfile = "test.csv"
with open(csvfile) as f:
    csv_reader = csv.DictReader(f, delimiter=',', quotechar='"', escapechar=None)
    for row in csv_reader:
        print(f'\t{row["device"]}\t{row["measurement"]}\t\t{row["value"]}')


with open(csvfile, mode='w') as f:
    csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["device", "measurement", "value"])
    csv_writer.writerow(["pi", "voltage", 1.5])
    csv_writer.writerow(["esp32", "current", 0.6])
    '''
    csv.QUOTE_ALL - Instructs writer objects to quote all fields.
    csv.QUOTE_MINIMAL - Instructs writer objects to only quote those fields which contain special characters such as delimiter, 
    quotechar or any of the characters in lineterminator.
    csv.QUOTE_NONNUMERIC - Instructs writer objects to quote all non-numeric fields. 
    Instructs the reader to convert all non-quoted fields to type float.
    csv.QUOTE_NONE - Instructs writer objects to never quote fields. When the current delimiter occurs in output data it is 
    preceded by the current escapechar character. If escapechar is not set, the writer will raise Error if any characters that 
    require escaping are encountered. Instructs reader to perform no special processing of quote characters.
    '''

# Dictionary to csv
with open(csvfile, mode='w') as f:
    cols = ["key1", "key2", "key3"]
    csv_writer = csv.DictWriter(f, fieldnames=cols)
    # fields list is used to write out the first row as column names
    csv_writer.writeheader()
    csv_writer.writerow({"key1": "pi", "key2": "voltage", "key3": 1.5})
    csv_writer.writerow({"key1": "esp32", "key2": "current", "key3": 0.6})
    # key1 could be 'device'
    # key2 could be 'measurement'
    # key3 could be 'value'

# Converting comma delimited to separate lines
with open(path.join(logDir, oFile), "w") as outfile:
    with open(path.join(logDir, iFile), "r") as infile:
        reader = csv.reader(infile)
        for row in reader:
            for x in range(int(row[1])):
                outfile.write("{0}\n".format(row[0]))
                print(row[0])

from array import array
import json

a = array('f', range(10))
a = {"key1":1, "key2":2}
f = open('test.csv', 'w')
with open('log.py', 'w') as f:
    json.dump(tuple(a), f)

json.dump(a, f)

f = open('test.csv', 'r')
with open('log.py', 'r') as f:
    z = array('f', json.load(f))

z = json.load(f)
print(z)
''' To use pickle just search/replace json with pickle

JSON (universal format that works with other languages like js) supports most Python data types
pickle (python specific) supports all python types
Have to convert arrays to tuple since it is not a native data type
'''
dir(os)
dir(f)
dir(str)
dir(list)
dir(dict)