#!/usr/bin/gnuplot

reset

# png
#set terminal pngcairo size 350,292 enhanced font 'Verdana,10'
#set output 'plotting_data1.png'

# svg
set terminal svg size 800,600 fname 'Verdana, Helvetica, Arial, sans-serif' fsize '10'
set output 'fullness.svg'

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#000000' lt 1 lw 2 pt 7 ps 1 # --- black for buffer
set style line 2 lc rgb '#DF0101' # --- red for mean value
set style line 3 lc rgb '#0B6121' # --- green for std dev
set style line 4 lc rgb '#CCCCCC' # --- gray for std dev
#unset key

set ytics 0.1
set yrange[0:1]
set tics scale 1

set xlabel "Number of Round"
set ylabel "Buffer Fullness (playback time)"

f1=filename

stats f1 using 2 name "A"
plot  f1 u 1:2 w l title columnheader(2) ls 4, f1 u 1:2 smooth bezier title columnheader(2) ls 1 , A_mean t "mean value" ls 2, A_stddev t "Std Dev" ls 3

set terminal x11
replot

#pause -1