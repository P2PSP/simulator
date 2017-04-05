# P2PSP simulator

[![Join the chat at https://gitter.im/P2PSP/Simulator](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/P2PSP/Simulator?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

A complete stand-alone simulator of the P2PSP protocol using Threads (or Processes) and message passing in order to do the prototyping of new strategies easier.

# Pre-requisites
## Linux
```
$ pip3 install fire
$ pip3 install matplotlib
$ pip3 install networkx
```

# Usage

```
$ ./simulator.py run --number-of-monitors NUMBER_OF_MONITORS --number-of-peers NUMBER_OF_PEERS \
--number-of-malicious NUMBER_OF_MALICIOUS --number-of-rounds NUMBER_OF_ROUNDS --drawing-log FILENAME \
--set-of-rules SET_OF_RULES
```
