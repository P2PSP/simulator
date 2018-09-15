#!/bin/bash

# Compute the average degree of the team versus the buffer size, which
# is ranged from 16=15+1 (by default) to 32 (by default).

buffer=32
cadence=0.001
link_loss_ratio=0.0
monitors=1
peers=15
rounds=500
set_of_rules=DBS

__debug__=1

usage() {
    echo $0
    echo "  [-b buffer size ($buffer)]"
    echo "  [-d chunk cadence ($cadence)]"
    echo "  [-l link lost ratio ($link_loss_ratio)]"
    echo "  [-m number of monitors ($monitors)]"
    echo "  [-p number of peers ($peers)]"
    echo "  [-r number of rounds ($rounds)]"
    echo "  [-s set of rules ($set_of_rules)]"
    echo "  [-? (help)]"
}

while getopts "b:d:l:m:p:r:s:?" opt; do
    case ${opt} in
        b)
            buffer="${OPTARG}"
	    echo buffer=$buffer
            ;;
        d)
            cadence="${OPTARG}"
	    echo cadence=$cadence
            ;;
        l)
            link_loss_ratio="${OPTARG}"
	    echo link_loss_ratio=$link_loss_ratio
            ;;
        m)
            monitors="${OPTARG}"
	    echo monitors=$monitors
            ;;
        p)
            peers="${OPTARG}"
	    echo peers=$peers
            ;;
        r)
            rounds="${OPTARG}"
	    echo rounds=$rounds
            ;;
        s)
            set_of_rules="${OPTARG}"
	    echo set_of_rules=$set_of_rules
            ;;
        ?)
            usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -${OPTARG}" >&2
            usage
            exit 1
            ;;
        :)
            echo "Option -${OPTARG} requires an argument." >&2
            usage
            exit 1
            ;;
    esac
done

if [ $__debug__ -eq 1 ]; then
    set -x
fi

dirname=../results/${buffer}_${cadence}_${link_loss_ratio}_${monitors}_${peers}_${rounds}_${set_of_rules}
mkdir $dirname
filename=$dirname/${0##*/}_`date "+%F-%T"`.txt
rm -f $filename
echo \# buffer_size=$buffer >> $filename
echo \# cadence=$cadence >> $filename
echo \# link_loss_ratio=$link_loss_ratio >> $filename
echo \# monitors=$monitors >> $filename
echo \# peers=$peers >> $filename
echo \# rounds=$rounds >> $filename
echo \# set=$set_of_rules >> $filename

iteration=$(($monitors+$peers))
while [ $iteration -le $buffer ]; do

    ./trace python3 -u ../src/simulator.py run --buffer_size $buffer --chunk_cadence $cadence --link_loss_ratio=$link_loss_ratio --number_of_monitors $monitors --number_of_peers $peers --number_of_rounds $rounds --set_of_rules $set_of_rules > /tmp/$iteration
    grep "average degree" /tmp/$iteration | cut -d " " -f 7 > /tmp/$iteration.dat
    average=`./average.py /tmp/$iteration.dat`
    echo -e $iteration'\t'$average >> $filename
    let iteration=iteration+1 

done

if [ $__debug__ -eq 1 ]; then
    set +x
fi

