#!/usr/bin/gnuplot

reset

# png
#set terminal pngcairo size 350,292 enhanced font 'Verdana,10'
#set output 'plotting_data1.png'

# svg
set terminal svg size 800,600 font "Verdana{10}"
set output 'team.svg'

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#0060ad' lt 1 lw 1 pt 6 ps 1 # --- blue for TPs
set style line 2 lc rgb '#0B6121' lt 1 lw 1 pt 8 ps 1 # --- gree for WIPs
set style line 3 lc rgb '#DF0101' lt 1 lw 1 pt 4 ps 1 # --- red for MPs

#unset key

set ytics 1
set tics scale 1

set xlabel "Number of Round"
set ylabel "Number of peers"

f1=filename

plot for [i=2:4] f1 u 1:i w lp title columnheader(i) ls i-1

set terminal x11
replot

#pause -1