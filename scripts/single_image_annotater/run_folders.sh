#!/bin/bash

# Parent directory containing all folders
PARENT_DIR="/data/jj/datasets/frames/frames_filtered"

# Loop through each main folder in the parent directory
for main_folder in "$PARENT_DIR"/*; do
    if [ -d "$main_folder" ]; then  # Check if it's a directory
        # Loop through each subfolder
        for subfolder in "$main_folder"/*; do
            if [ -d "$subfolder" ]; then  # Check if it's a directory
                # Create output folder path
                OUTPUT_FOLDER="$subfolder/gpt_annotations"
                
                # Create output directory if it doesn't exist
                mkdir -p "$OUTPUT_FOLDER"
                
                # Check if output directory already has files
                if [ -z "$(ls -A $OUTPUT_FOLDER)" ]; then
                    echo "Processing subfolder: $subfolder"
                    # Run the Python script for each subfolder
                    python /data/jj/proj/EndoGPT/image_annotator.py --input "$subfolder" --output-dir "$OUTPUT_FOLDER" --sampling 1
                else
                    echo "Skipping subfolder: $subfolder (already processed)"
                fi
            fi
        done
    fi
done

# Remove all gpt_annotations folders
#find /data/jj/datasets/frames/frames_filtered -type d -name "gpt_annotations" -exec rm -rf {} +