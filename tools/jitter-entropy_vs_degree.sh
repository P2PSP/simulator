#!/bin/bash

# Compute the entropy of the jitter (measured in chunks, not in time)
# as a function of the neighborhood degree.

buffer=32
cadence=0.01
max_degree=5
link_loss_ratio=0.0
monitors=1
peers=9
rounds=100
set_of_rules=DBS

__debug__=1

usage() {
    echo $0
    echo "  [-b buffer size ($buffer)]"
    echo "  [-d chunk cadence ($cadence)]"
    echo "  [-e max degree ($max_degree)]"
    echo "  [-l link lost ratio ($link_loss_ratio)]"
    echo "  [-m number of monitors ($monitors)]"
    echo "  [-p number of peers ($peers)]"
    echo "  [-r number of rounds ($rounds)]"
    echo "  [-s set of rules ($set_of_rules)]"
    echo "  [-? (help)]"
}

while getopts "b:d:l:e:m:p:r:s:?" opt; do
    case ${opt} in
        b)
            buffer="${OPTARG}"
	    echo buffer=$buffer
            ;;
        d)
            cadence="${OPTARG}"
	    echo cadence=$cadence
            ;;
        e)
            max_degree="${OPTARG}"
	    echo max_degree=$max_degree
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

dirname=../results/${buffer}_${cadence}_${link_loss_ratio}_${max_degree}_${monitors}_${peers}_${rounds}_${set_of_rules}
mkdir $dirname
filename=$dirname/${0##*/}_`date "+%F-%T"`.txt
rm -f $filename
echo \# buffer_size=$buffer >> $filename
echo \# cadence=$cadence >> $filename
echo \# link_loss_ratio=$link_loss_ratio >> $filename
echo \# monitors=$monitors >> $filename
echo \# peers=$peers >> $filename
echo \# number_of_rounds=$rounds >> $filename
echo \# set_of_rules=$set_of_rules >> $filename

iteration=1
while [ $iteration -le $max_degree ]; do

    ./trace python3 -u ../src/simulator.py run --buffer_size $buffer --chunk_cadence $cadence --link_loss_ratio=$link_loss_ratio --max_degree=$iteration --number_of_monitors $monitors --number_of_peers $peers --number_of_rounds $rounds --set_of_rules $set_of_rules --log=INFO 2> /tmp/$iteration

    grep "delta of chunk" /tmp/$iteration | cut -d " " -f 9 > /tmp/$iteration.dat
    entropy=`./entropy.py /tmp/$iteration.dat $buffer`
    echo -e $iteration'\t'$entropy >> $filename
    echo "Pulse enter to continue ..."
    read
    let iteration=iteration+1 

done

if [ $__debug__ -eq 1 ]; then
    set +x
fi

