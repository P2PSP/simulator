tail -n 401 < averages.txt > CLR_vs_B_N100.txt

gnuplot << EOF
set terminal cairolatex eps
set output "/tmp/CLR_vs_B_N100.tex"
set title "20~ms of latency"
set ylabel "CLR"
set xlabel "\$B\$"
set key left
set yrange [0:0.15]
plot "CLR_vs_B_N100.txt" using 2:3 smooth bezier title "" 
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
\resizebox{1.0\\textwidth}{!}{\\input{/tmp/CLR_vs_B_N100}}
\end{document}
EOF
dvips texput.dvi -o /tmp/texput.ps
ps2eps --loose < /tmp/texput.ps > /tmp/texput.eps
epstopdf /tmp/texput.eps
mv /tmp/texput.pdf CLR_vs_B_N100.pdf
