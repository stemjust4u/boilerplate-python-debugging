import pandas as pd
from os import path
from pathlib import Path

debugging_dir = path.join(path.dirname(path.dirname(path.realpath(__file__))), 'debugging')
datafile = path.join(debugging_dir, "largedata.log")
data = pd.read_csv(datafile, low_memory=False)
print("Total rows: {0}".format(len(data)))
print(list(data))


accidents_sunday = data[data.Day_of_Week == 1]
print("Accidents which happened on a Sunday: {0}".format(
    len(accidents_sunday)))