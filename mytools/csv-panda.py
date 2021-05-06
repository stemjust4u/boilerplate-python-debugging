# python3.7 -m pip install pandas
import pandas
import csv
from datetime import datetime

print(datetime.now().microsecond) # will print only the microsecond portion

csvfile = "dftest.csv"
with open(csvfile, mode='w') as f:
    csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["date", "device", "measurement", "value"])
    csv_writer.writerow([datetime.now(), "pi", "voltage", 1.5])
    csv_writer.writerow([datetime.now(),"esp32", "current", 0.6])
    csv_writer.writerow([datetime.now(),"esp32", "voltage", 1.6])

import pandas
df = pandas.read_csv(csvfile, index_col='device', parse_dates=['date'])
print(df)

print(type(df['date'][0])) # confirm it is a date

# to follow influx criteria.. data inserted as a tag is indexed and data inserted as a field is not
df = pandas.read_csv(csvfile, parse_dates=['date'])   # multi index
multidf = df.set_index(['device', 'measurement'])
print(multidf)

# Can use own header name or change header name. If changing header tell pandas to ignore current with header=0
df = pandas.read_csv(csvfile, 
            index_col='newdevice',  # Have to update name since changing with 'names'
            parse_dates=['newdate'],# Have to update name since changing with 'names'  
            header=0,
            names=['newdate', 'newdevice', 'newmeas', 'newvalue'])
print(df)

# write data back to csv
df.to_csv('testmod1.csv')
multidf.to_csv('testmulti.csv')
