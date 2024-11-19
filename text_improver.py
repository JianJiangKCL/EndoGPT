import argparse
from openai import OpenAI
import os
from typing import List, Dict
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from datetime import datetime
import concurrent.futures

# Load environment variables
load_dotenv()

from utils.key_loader import load_api_keys

# Load environment variables
load_dotenv()

# Load encrypted keys
api_keys = load_api_keys()
api_key = api_keys['OPENAI_API_KEY']

class TextImprover:
    def __init__(self):
        """Initialize the TextImprover with OpenAI client."""
        self.client = OpenAI(api_key=api_key)  # Use the loaded api_key instead of env variable
        self.rate_limit = 3  # seconds between requests
        self.last_request_time = 0

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def improve_text(self, text: str, language: str = "chinese") -> str:
        """
        Improve text readability using OpenAI API.
        
        Args:
            text (str): Input text to improve
            language (str): Language of the text (default: "chinese")
            
        Returns:
            str: Improved text with better formatting and punctuation
        """
        prompt = f"""Please improve the readability of the following Chinese text.
        This is an audio transcription of an endoscopy procedure with simultaneous doctor commentary.
        The text likely contains typos, medical terminology, and formatting issues that need to be fixed.
        
        Key requirements:
        1. Fix any spelling mistakes and typos in Chinese characters, especially medical terms
        2. Add proper punctuation (using Chinese punctuation marks)
        3. Improve formatting for better readability while preserving the procedural flow
        4. Maintain the original medical meaning and technical accuracy
        5. Keep any timestamps, measurements, and numbers unchanged
        6. Preserve speaker transitions and commentary structure
        
        Text to improve:
        {text}
        """

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that improves text readability while maintaining the original meaning."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content

    def process_file(self, input_file: str, output_file: str = None, chunk_size: int = 2000) -> None:
        """
        Process a text file in chunks and improve its readability.
        
        Args:
            input_file (str): Path to input file
            output_file (str): Path to output file (optional)
            chunk_size (int): Number of characters per chunk
        """
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_base = os.path.splitext(input_file)[0]
            output_file = f"{file_base}_improved_{timestamp}.txt"

        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

        # Process text in chunks
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

        # Process chunks concurrently
        improved_chunks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Create a list of future objects
            future_to_chunk = {executor.submit(self.improve_text, chunk): i 
                             for i, chunk in enumerate(chunks)}
            
            # Process completed futures as they complete
            print(f"Processing {len(chunks)} chunks concurrently...")
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_index = future_to_chunk[future]
                try:
                    improved_chunk = future.result()
                    improved_chunks.append((chunk_index, improved_chunk))
                    print(f"Completed chunk {chunk_index + 1}/{len(chunks)}")
                except Exception as e:
                    print(f"Chunk {chunk_index + 1} generated an exception: {e}")

        # Sort chunks back into original order and combine
        improved_chunks.sort(key=lambda x: x[0])
        improved_text = '\n'.join(chunk[1] for chunk in improved_chunks)

        # Write improved text to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(improved_text)

        print(f"Improved text saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Improve text readability using OpenAI API')
    parser.add_argument('input_file', help='Path to input text file')
    parser.add_argument('--output_file', help='Path to output file (optional)')
    parser.add_argument('--chunk_size', type=int, default=2000, help='Number of characters per chunk')
    
    args = parser.parse_args()
    
    improver = TextImprover()
    improver.process_file(args.input_file, args.output_file, args.chunk_size)

if __name__ == "__main__":
    main() 