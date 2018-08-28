#!/bin/bash

buffer=20
delay=0.05
monitors=1
peers=10
rounds=100

__debug__=0

usage() {
    echo $0
    echo "  [-b buffer size ($buffer)]"
    echo "  [-d chunk delay ($delay)]"
    echo "  [-m number of monitors ($monitors)]"
    echo "  [-p number of peers ($peers)]"
    echo "  [-r number of rounds ($rounds)]"
    echo "  [-? (help)]"
}

while getopts "b:d:m:p:r:?" opt; do
    case ${opt} in
        b)
            buffer="${OPTARG}"
	    echo buffer=$buffer
            ;;
        d)
            delay="${OPTARG}"
	    echo delay=$delay
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

working_dir=$buffer_$delay_$monitors_$peers_$rounds.txt
rm -rf $working_dir
mkdir $working_dir

filename=$working_dir/$iteration.txt
    
echo \# monitors=$monitors >> $filename
echo \# peers=$peers >> $filename
echo \# rounds=$rounds >> $filename
echo \# delay=$delay >> $filename

iteration=1
while [ $iteration -le $buffer ]; do

    python3 -u ../src/simulator.py run --set_of_rules DBS --number_of_monitors $monitors --number_of_peers $peers --number_of_rounds $rounds --buffer_size $iteration --chunk_delay $delay 2> /tmp/1

    CLR=`grep CLR /tmp/1 | cut -d "=" -f 2 | cut -d " " -f 1`

    echo -e $iteration'\t'$CLR >> $filename

    let iteration=iteration+1 

done


if [ $__debug__ -eq 1 ]; then
    set +x
fi

