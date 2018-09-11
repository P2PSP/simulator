default:	all

../../FIGs/latency_vs_team_size_flash_crowd_256.fig:	flash_crowd_256/*.dat flash_crowd_256/total_mcast_average.dat flash_crowd_256/total_hello_average.dat
	./latency_vs_team_size.sh flash_crowd_256 `cat flash_crowd_256/total_average_mcast.dat` `cat flash_crowd_256/total_average_hello.dat`

../../FIGs/latency_vs_team_size_flash_crowd_128.fig:	flash_crowd_128/*.dat flash_crowd_128/total_mcast_average.dat flash_crowd_128/total_hello_average.dat
	./latency_vs_team_size.sh flash_crowd_128 `cat flash_crowd_128/total_average_mcast.dat` `cat flash_crowd_128/total_average_hello.dat`

../../FIGs/latency_vs_team_size_slow_arrivals_256.fig:	slow_arrivals_256/*.dat slow_arrivals_256/total_mcast_average.dat slow_arrivals_256/total_hello_average.dat
	./latency_vs_team_size.sh slow_arrivals_256 `cat slow_arrivals_256/total_average_mcast.dat` `cat slow_arrivals_256/total_average_hello.dat`

../../FIGs/latency_vs_team_size_slow_arrivals_128.fig:	slow_arrivals_128/*.dat slow_arrivals_128/total_mcast_average.dat slow_arrivals_128/total_hello_average.dat
	./latency_vs_team_size.sh slow_arrivals_128 `cat slow_arrivals_128/total_average_mcast.dat` `cat slow_arrivals_128/total_average_hello.dat`

flash_crowd_256/average_mcast.dat:	flash_crowd_256/mcast??.dat 
	./average.py -d flash_crowd_256/ -b mcast

flash_crowd_256/average_hello.dat:	flash_crowd_256/hello??.dat 
	./average.py -d flash_crowd_256/ -b hello

flash_crowd_128/average_mcast.dat:	flash_crowd_128/mcast??.dat 
	./average.py -d flash_crowd_128/ -b mcast

flash_crowd_128/average_hello.dat:	flash_crowd_128/hello??.dat 
	./average.py -d flash_crowd_128/ -b hello

slow_arrivals_256/average_mcast.dat:	slow_arrivals_256/mcast??.dat 
	./average.py -d slow_arrivals_256/ -b mcast

slow_arrivals_256/average_hello.dat:	slow_arrivals_256/hello??.dat 
	./average.py -d slow_arrivals_256/ -b hello

slow_arrivals_128/average_mcast.dat:	slow_arrivals_128/mcast??.dat 
	./average.py -d slow_arrivals_128/ -b mcast

slow_arrivals_128/average_hello.dat:	slow_arrivals_128/hello??.dat 
	./average.py -d slow_arrivals_128/ -b hello

flash_crowd_256/total_mcast_average.dat:	flash_crowd_256/average_mcast.dat
	./total_average.py -d flash_crowd_256/ -b mcast

flash_crowd_256/total_hello_average.dat:	flash_crowd_256/average_hello.dat
	./total_average.py -d flash_crowd_256/ -b hello

flash_crowd_128/total_mcast_average.dat:	flash_crowd_128/average_mcast.dat
	./total_average.py -d flash_crowd_128/ -b mcast

flash_crowd_128/total_hello_average.dat:	flash_crowd_128/average_hello.dat
	./total_average.py -d flash_crowd_128/ -b hello

slow_arrivals_256/total_mcast_average.dat:	slow_arrivals_256/average_mcast.dat
	./total_average.py -d slow_arrivals_256/ -b mcast

slow_arrivals_256/total_hello_average.dat:	slow_arrivals_256/average_hello.dat
	./total_average.py -d slow_arrivals_256/ -b hello

slow_arrivals_128/total_mcast_average.dat:	slow_arrivals_128/average_mcast.dat
	./total_average.py -d slow_arrivals_128/ -b mcast

slow_arrivals_128/total_hello_average.dat:	slow_arrivals_128/average_hello.dat
	./total_average.py -d slow_arrivals_128/ -b hello

all:	../../FIGs/latency_vs_team_size_flash_crowd_256.fig \
	../../FIGs/latency_vs_team_size_slow_arrivals_256.fig \
	../../FIGs/latency_vs_team_size_flash_crowd_128.fig \
	../../FIGs/latency_vs_team_size_slow_arrivals_128.fig \
	flash_crowd_256/total_hello_average.dat \
	flash_crowd_256/total_mcast_average.dat \
	flash_crowd_128/total_hello_average.dat \
	flash_crowd_128/total_mcast_average.dat \
	slow_arrivals_256/total_hello_average.dat \
	slow_arrivals_256/total_mcast_average.dat \
	slow_arrivals_128/total_hello_average.dat \
	slow_arrivals_128/total_mcast_average.dat 


default:	all

clean:
	rm -f ../../FIGs/latency_vs_team_size_flash_crowd_256.fig \
	../../FIGs/latency_vs_team_size_slow_arrivals_256.fig \
	../../FIGs/latency_vs_team_size_flash_crowd_128.fig \
	../../FIGs/latency_vs_team_size_slow_arrivals_128.fig \
	flash_crowd_256/total_hello_average.dat \
	flash_crowd_128/total_mcast_average.dat \
	slow_arrivals_256/total_hello_average.dat \
	slow_arrivals_128/total_mcast_average.dat
