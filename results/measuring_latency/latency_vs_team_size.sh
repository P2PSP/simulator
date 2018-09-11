DIRECTORY=$1
TOTAL_AVERAGE_MCAST=$2
TOTAL_AVERAGE_HELLO=$3

gnuplot << EOF
#set terminal svg;
set terminal fig color solid;
#set output "$DIRECTORY/latency_vs_team_size.svg";
set output "../figs/latency_vs_team_size_$DIRECTORY.fig";
set xlabel "Number of peers";
set ylabel "Latency (seconds)";
#set grid;
set xrange [0:100];
a(x) = b*x + c;
d(x) = e*x + f;
fit a(x) "$DIRECTORY/average_mcast.dat" using 1:2 via b,c;
fit d(x) "$DIRECTORY/average_hello.dat" using 1:2 via e,f;
plot \
"$DIRECTORY/mcast00.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast01.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast02.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast03.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast04.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast05.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast06.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast07.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast08.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/mcast09.dat" with points ps 0.4 lt 16 title "", \
"$DIRECTORY/average_mcast.dat" with lines lt 0 title "", \
"$DIRECTORY/hello00.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello01.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello02.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello03.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello04.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello05.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello06.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello07.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello08.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/hello09.dat" with points ps 0.4 lt 19 title "", \
"$DIRECTORY/average_hello.dat" with lines lt 1 title "", \
a(x) lt 0 title "IP Multicast ($TOTAL_AVERAGE_MCAST)", \
d(x) lt 1 title "Hello ($TOTAL_AVERAGE_HELLO)"
EOF

