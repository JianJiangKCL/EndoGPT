#!/bin/bash

# Define the path to your parent directory
PARENT_DIR="/data/jj/datasets/frames/frames_filtered"

# Run the Python script with full structure mode
python /data/jj/proj/EndoGPT/concat_images.py --full "$PARENT_DIR"

echo "Full structure processing completed!" 