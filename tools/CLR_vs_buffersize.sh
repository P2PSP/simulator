#!/bin/bash

buffer=32
cadence=0.01
monitors=1
peers=9
rounds=100

__debug__=1

usage() {
    echo $0
    echo "  [-b buffer size ($buffer)]"
    echo "  [-d chunk cadence ($cadence)]"
    echo "  [-m number of monitors ($monitors)]"
    echo "  [-p number of peers ($peers)]"
    echo "  [-r number of rounds ($rounds)]"
    echo "  [-? (help)]"
}

while getopts "b:c:m:p:r:?" opt; do
    case ${opt} in
        b)
            buffer="${OPTARG}"
	    echo buffer=$buffer
            ;;
        d)
            cadence="${OPTARG}"
	    echo cadence=$cadence
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

dirname=${buffer}_${cadence}_${monitors}_${peers}_${rounds}
mkdir $dirname
filename=$dirname/`date "+%F-%T"`.txt
rm -f $filename
echo \# monitors=$monitors >> $filename
echo \# peers=$peers >> $filename
echo \# rounds=$rounds >> $filename
echo \# cadence=$cadence >> $filename

iteration=1
while [ $iteration -le $buffer ]; do

    python3 -u ../src/simulator.py run --set_of_rules DBS --number_of_monitors $monitors --number_of_peers $peers --number_of_rounds $rounds --buffer_size $iteration --chunk_cadence $cadence > /tmp/$iteration

    lost_chunks=`grep "lost chunks" /tmp/$iteration | cut -d " " -f 3`
    sent_chunks=`grep "lost chunks" /tmp/$iteration | cut -d " " -f 7`
    CLR=`echo $lost_chunks/$sent_chunks | bc -l`
    
    echo -e $iteration'\t'$lost_chunks'\t'$sent_chunks'\t'$CLR >> $filename

    let iteration=iteration+1 

done

if [ $__debug__ -eq 1 ]; then
    set +x
fi

