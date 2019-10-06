#!/bin/bash

gnuplot << EOF
set terminal cairolatex eps
set output "/tmp/CLR_vs_N_and_B_lat.tex"
set title "20~ms of latency"
set xlabel "\$N^*\$"
set ylabel "\$B\$"
set cblabel "CLR"
set key left
set xrange [10:100]
set yrange [20:600]
set cbrange [0:1]
set ytics 20 30
plot "averages.txt" with image title "", 2*x title "\$~~~B=2N^*\$", 3*x title "\$B=3N^*\$", 4*x title "\$B=4N^*\$", 6*x title "\$B=6N^*\$" 
EOF

latex << EOF
\documentclass{minimal}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
%\usepackage{color}
%\usepackage{microtype}
\begin{document}
\pagestyle{empty}
\thispagestyle{empty}
\resizebox{1.0\\textwidth}{!}{\\input{/tmp/CLR_vs_N_and_B_lat}}
\end{document}
EOF
dvips texput.dvi -o /tmp/texput.ps
ps2eps --loose < /tmp/texput.ps > /tmp/texput.eps
epstopdf /tmp/texput.eps
mv /tmp/texput.pdf CLR_vs_N_and_B_lat.pdf
