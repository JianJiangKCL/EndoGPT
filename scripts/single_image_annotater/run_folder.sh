#!/bin/bash

# Fixed paths for input and output folders
# INPUT_FOLDER="/data/jj/proj/EndoGPT/7095/7095"
# OUTPUT_FOLDER="/data/jj/proj/EndoGPT/7095/results"
INPUT_FOLDER="/data/jj/proj/EndoGPT/5596"
OUTPUT_FOLDER="/data/jj/proj/EndoGPT/5596/results"
# Run the Python script
python gpt_api.py --input "$INPUT_FOLDER" --output-dir "$OUTPUT_FOLDER" --sampling 20