# P2PSP Simulator Tools

Go to tools directory:
```
$ cd tools
```
Current available tools are:
## Plot.sh
`plot.sh` is a script which plot the team and the buffer status of the complete simulation doing use of:
- drawtodat.py to convert the drawing log file into a dat format.
- plot_team.gp which is a gnuplot script to plot the team status.
- plot_buffer.gp which is a gnuplot script to plot the buffer status.

### Usage
```
$ ./plot.sh <drawing_log_file>
```
- drawing_log_file: output drawing_log file generated with simulator.py

## Pollute.py
`pollute.py` is a script which simulate the loss of chunks in a video file. It helps us to get an idea about the maximun aceptable CLR (Chunk Lost Rate) for an specific media content.

### Usage
```
pollute.py -i <inputfile> -o <outputfile> -c <chunk_size> -a <number_of_attackers> -n <team_size> -m <mode>
```
- inputfile: a video file as a input.
- outputfile: where your output file is stored. It will contain lost chunks.
- chunk_size: size of the chunk in bytes.
- number_of_attackers: number of mailicious peers attacking to the team. It is equal to the number of lost chunk for each round.
- team_size: size of the team.
- mode: it is a number between 0 and 2.
  - (0) The lost chunk is replaced by a chunk with zeros. (default).
  - (1) The lost chunk is replaced by the last valid chunk.
  - (2) The lost chunk is replaced by nothing. Then, if the lost chunk is the number 4,the stream looks like 01235678...
