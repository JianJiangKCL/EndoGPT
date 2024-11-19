#!/bin/bash

# Define the path to your single folder
SINGLE_FOLDER="/data/jj/datasets/frames/frames_filtered/websurg/4201"

# Run the Python script with single folder mode
python /data/jj/proj/EndoGPT/concat_images.py --single "$SINGLE_FOLDER"

echo "Single folder processing completed!" 