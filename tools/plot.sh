#!/bin/bash
echo "Generating dat files..."
# Get dat files from draw
python drawtodat.py -i $1
echo "Done"

# Plot Team
echo "Plotting Team..."
gnuplot -persist -e "filename='$(basename $1).team'" plot_team.gp
echo "Done"

# Plot Buffer
echo "Plotting Buffer..."
gnuplot -persist -e "filename='$(basename $1).buffer'" plot_buffer.gp
echo "Done"
