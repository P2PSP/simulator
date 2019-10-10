gnuplot << EOF
set terminal cairolatex eps
set output "/tmp/CLR_vs_B.tex"
set xlabel "\$B\$"
set ylabel "CLR"
set key right
set xrange [10:1000]
plot "DBS.txt" with lines title "full-connected", "DBS2.txt" with lines title "optimized"
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
\resizebox{1.0\\textwidth}{!}{\\input{/tmp/CLR_vs_B}}
\end{document}
EOF
dvips texput.dvi -o /tmp/texput.ps
ps2eps --loose < /tmp/texput.ps > /tmp/texput.eps
epstopdf /tmp/texput.eps
mv /tmp/texput.pdf CLR_vs_B.pdf
