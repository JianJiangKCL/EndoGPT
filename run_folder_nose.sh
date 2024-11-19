#!/bin/bash

# Fixed paths for input and output folders
INPUT_FOLDER="/data/jj/proj/EndoGPT/NOSE"
OUTPUT_FOLDER="/data/jj/proj/EndoGPT/NOSE/results"

read -r -d '' PROMPT << 'EOL'
I will show you two images:
1. A reference image showing both anatomical landmarks AND example cases for each score (1-4)
2. The endoscopic image to be analyzed

Compare the test image directly with the reference examples while following these scoring criteria:

Score 4 - Like Reference Example 4:
- Complete/near-complete blockage of lower nasal cavity
- Massive polyps filling the entire visible space
- No clear air passage visible

Score 3 - Like Reference Example 3:
- Polyps extend BEYOND middle turbinate lower edge
- Reaches or approaches lower turbinate
- Partial but not complete obstruction
- Compare directly with Example 3's extension pattern

Score 2 - Like Reference Example 2:
- Polyps align EXACTLY with middle turbinate lower edge
- Similar appearance to Example 2's alignment
- Does not extend significantly beyond this point
- Lower nasal cavity remains visible

Score 1 - Like Reference Example 1:
- Small polyps in middle meatus
- Does NOT reach middle turbinate lower edge
- Compare size and position with Example 1
- Clear lower nasal cavity

EVALUATION PROCESS:
1. First compare the test image with all reference examples
2. Find the closest matching reference example
3. Verify that the anatomical criteria for that score are met
4. Double-check against adjacent scores' examples

FORMAT YOUR RESPONSE AS:
Score: [number]
Primary Findings:
- Lower nasal cavity status: [clear/partially obstructed/completely obstructed]
- Polyp lower edge position: [precise anatomical position]
- Olfactory cleft involvement: [only if relevant]

Justification: [include comparison to reference examples]
Key Anatomical References: [specific landmarks used]
EOL

# Run the Python script
python gpt_nose.py --input "$INPUT_FOLDER" --output-dir "$OUTPUT_FOLDER" --prompt "$PROMPT"