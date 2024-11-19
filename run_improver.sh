#!/bin/bash

# Path to your Python script and input file
INPUT_FILE="/data/jj/proj/EndoGPT/chinese.txt"

# Run the Python script
python3 text_improver.py $INPUT_FILE

# Make the script executable with:
# chmod +x run_improver.sh 