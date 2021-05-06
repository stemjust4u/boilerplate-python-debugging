# python-nodered-mqtt-boilerplate
Template for setting up python-nodered link via mqtt


Profiling
Python
* perf_counter_ns (quick t1 - t0. _ns will use nano sec, integer, helps reduce floating point errors)
* from timer import Timer, as decorator --> use @Timer(name="test", units="us")  
* from timer import Timer, as Class     --> t=Timer(name="test", units="ms") then t.start() and t.stop()
* timeit (useful for comparing short snippets. ie to compare time delta between txt.split and txt.partition)
* cprofile - find hotspots in the program. Isolate which functions to look at.
* lineprofile - detailed, by line analysis of the function

$ python3.7 -m cProfile -o testing.prof debugging_tools.py
$ python3.7 -m pstats testing.prof

testing.prof% help
testing.prof% strip
testing.prof% sort cumtime
testing.prof% stats 10

testing.prof% sort tottime
testing.prof% stats 10

testing.prof% stats <function name>

To convert the .prof and open KCacheGrind to analyze the data
$ pyprof2calltree -k -i testing.prof

Line profiling add overhead to the runtime. First use cProfile to isolate which functions to look at and then line_profiler on those functions to get details.. 
line profile installation instructions
git clone https://github.com/rkern/line_profiler.git
find line_profiler -name '*.pyx' -exec cython {} \;
cd line_profiler
pip install . --user

Before you run the profiler, you need to tell it which functions to profile. You do this by adding a @profile decorator inside your source code. 


@profile                    # Delete when you're done
def function():
    print('stuff here')

Then run with
$ kernprof -l latest_tutorial.py

The default behavior of kernprof is to put the results into a binary file script_to_profile.py.lprof . You can tell kernprof to immediately view the formatted results at the terminal with the [-v/--view] option. Otherwise, you can view the results later like so:

$ python3.7 -m line_profiler script_to_profile.py.lprof

Time will be in msec