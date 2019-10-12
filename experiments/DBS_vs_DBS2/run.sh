B2=25 # Max buffer size
B1=15 # Min buffer size
N=10  # Num peers

rm *.txt
./simulate.sh $B2 $B1 $N
./compute_averages.sh DBS $B2 $B1 $N > DBS.txt
./compute_averages.sh DBS2 $B2 $B1 $N > DBS2.txt
