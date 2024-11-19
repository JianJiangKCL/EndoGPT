import base64
import requests
from openai import OpenAI
from PIL import Image
from io import BytesIO
import argparse
import os
import json
import time
from datetime import datetime
from typing import Dict
import concurrent.futures
from dotenv import load_dotenv
from utils.key_loader import load_api_keys
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Load encrypted keys
api_keys = load_api_keys()
api_key = api_keys['OPENAI_API_KEY']
MAX_WORKERS = 4

class ImageAnalyzer:
    def __init__(self):
        """
        Initialize the ImageAnalyzer with the fixed API key.
        """
        self.client = OpenAI(api_key=api_key)
        # Rate limit: 10 images per minute (1 every 6 seconds to be safe)
        self.rate_limit = 6  # seconds between requests
        self.last_request_time = 0

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def analyze_local_image(self, image_path, prompt="What's in this image?", ref_image_path="/data/jj/proj/EndoGPT/ref.png"):
        """Analyze image with rate limiting and retry logic, including a reference image"""
        try:
            # Ensure we respect rate limits
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)
            
            self.last_request_time = time.time()
            
            # Read and encode both images
            with open(image_path, "rb") as image_file:
                input_image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            with open(ref_image_path, "rb") as ref_file:
                ref_image_data = base64.b64encode(ref_file.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Here is a reference image:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{ref_image_data}"
                                }
                            },
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{input_image_data}"
                                }
                            }
                        ],
                    }
                ],
                max_tokens=3000,
            )
            return response.choices[0].message.content

        except Exception as e:
            if "rate_limit" in str(e).lower():
                # If we hit rate limit, wait and retry
                time.sleep(self.rate_limit)
                raise  # Let retry decorator handle it
            return f"Error analyzing image: {str(e)}"

    def analyze_folder(
        self,
        folder_path: str,
        prompt: str,
        output_dir: str = None,
        supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.gif'),
        save_results: bool = True,
        batch_size: int = 10,
        sampling: int = 5
    ) -> Dict[str, str]:
        """
        Analyze all images in a folder using parallel processing.

        Args:
            folder_path (str): Path to the folder containing images
            prompt (str): Question or instruction about the images
            output_dir (str, optional): Directory to save results. If None, uses folder_path/results
            supported_formats (tuple): Tuple of supported image file extensions
            save_results (bool): Whether to save results to a JSON file
            batch_size (int): Number of images to process in parallel
            sampling (int): Process every Nth frame. Default=1 means process all frames.
                           sampling=2 means process every other frame, etc.

        Returns:
            Dict[str, str]: Dictionary mapping image paths to their analysis results
        """
        # Ensure folder path exists
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder path does not exist: {folder_path}")

        # Setup output directory
        if output_dir is None:
            output_dir = os.path.join(folder_path, 'results')
        os.makedirs(output_dir, exist_ok=True)

        # Get list of image files and sort numerically
        def extract_number(filename):
            # Extract numbers from filename, default to 0 if no numbers found
            return int(''.join(filter(str.isdigit, filename)) or 0)

        image_files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
            and f.lower().endswith(supported_formats)
        ]
        image_files.sort(key=extract_number)  # Sort based on numerical value in filename

        # After sorting, apply sampling to image_files
        image_files = image_files[::sampling]  # Take every Nth item

        if not image_files:
            raise ValueError(f"No supported image files found in {folder_path}")

        # Create full paths for images (maintaining sorted order)
        image_paths = [os.path.join(folder_path, f) for f in image_files]

        # Setup output file early
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"analysis_results_{timestamp}.json")
        
        # Initialize results file with header
        initial_summary = {
            "processing_stats": {
                "total_images": len(image_files),
                "timestamp_start": datetime.now().isoformat(),
            },
            "results": {}
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(initial_summary, f, indent=2, ensure_ascii=False)

        # Initialize progress bar
        pbar = tqdm(total=len(image_paths), desc="Processing images")
        start_time = datetime.now()
        results = {}

        def process_single_image(image_path):
            max_retries = 3
            retry_delay = 10  # seconds
            
            for attempt in range(max_retries):
                try:
                    result = self.analyze_local_image(image_path, prompt)
                    return os.path.basename(image_path), result
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return os.path.basename(image_path), f"Error processing image after {max_retries} attempts: {str(e)}"

        # Process images with results saving
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_to_paths = {
                executor.submit(process_single_image, path): path 
                for path in image_paths
            }
            
            for future in tqdm(concurrent.futures.as_completed(futures_to_paths), 
                             total=len(image_paths), 
                             desc="Processing images"):
                image_name, result = future.result()
                results[image_name] = result
                
                # Save intermediate results with atomic write
                if save_results:
                    temp_output_file = output_file + '.tmp'
                    current_data = {
                        "processing_stats": {
                            "total_images": len(image_paths),
                            "timestamp_start": start_time.isoformat(),
                            "last_updated": datetime.now().isoformat()
                        },
                        "results": results
                    }
                    # Atomic write to prevent corruption
                    with open(temp_output_file, 'w', encoding='utf-8') as f:
                        json.dump(current_data, f, indent=2, ensure_ascii=False)
                    os.replace(temp_output_file, output_file)

        # Update final statistics
        end_time = time.time()
        total_time = end_time - start_time.timestamp()
        avg_time_per_image = total_time / len(image_files)

        with open(output_file, 'r+', encoding='utf-8') as f:
            final_data = json.load(f)
            final_data["processing_stats"].update({
                "total_time_seconds": round(total_time, 2),
                "avg_time_per_image_seconds": round(avg_time_per_image, 2),
                "timestamp_end": datetime.now().isoformat(),
            })
            f.seek(0)
            json.dump(final_data, f, indent=2, ensure_ascii=False)
            f.truncate()

        # Print processing summary
        print(f"\nProcessing Summary:")
        print(f"Total images processed: {len(image_files)}")
        print(f"Total processing time: {round(total_time, 2)} seconds")
        print(f"Average time per image: {round(avg_time_per_image, 2)} seconds")
        print(f"Results saved to: {output_file}")

        # Retry failed images
        failed_images = {
            name: path for name, path in zip(image_files, image_paths)
            if "Error processing image" in results.get(name, "")
        }
        
        if failed_images:
            print(f"\nRetrying {len(failed_images)} failed images...")
            for name, path in failed_images.items():
                try:
                    _, result = process_single_image(path)
                    results[name] = result
                    # Update results file
                    if save_results:
                        current_data = {
                            "processing_stats": {
                                "total_images": len(image_paths),
                                "timestamp_start": start_time.isoformat(),
                                "last_updated": datetime.now().isoformat()
                            },
                            "results": results
                        }
                        with open(output_file + '.tmp', 'w', encoding='utf-8') as f:
                            json.dump(current_data, f, indent=2, ensure_ascii=False)
                        os.replace(output_file + '.tmp', output_file)
                except Exception as e:
                    print(f"Final retry failed for {name}: {str(e)}")

        return results

#test
def main():
    parser = argparse.ArgumentParser(description='Analyze endoscopic images using GPT-4 Vision')
    parser.add_argument('--input', required=True, help='Input image file or directory')
    parser.add_argument('--output-dir', help='Output directory for results (optional)')
    parser.add_argument('--sampling', type=int, default=1, 
                       help='Process every Nth frame. Default=1 means process all frames. '
                            'sampling=2 means process every other frame, etc.')
    parser.add_argument('--prompt', default="Please analyze this image and provide response in EXACTLY the following format:\n\n"
                       "If this is a valid endoscopic image, output MUST be in this format:\n"
                       "Tissue: [describe visible tissue and anatomical structures]\n"
                       "Tools: [list all visible medical instruments in detail - e.g. biopsy forceps, snare, injection needle, clip applicator, etc. Write 'none' if no tools visible]\n"
                       "Abnormalities: [list any abnormalities from: inflammation/lesions/polyps/growths/color changes/bleeding, or 'none' if none visible]\n"
                       "ImageQuality: [describe any quality issues using following format - \n" 
                       "Blur: none/partial/severe (specify if due to movement)\n"
                       "Lighting: normal/dark/overexposed\n"
                       "Visibility: clear/partially obscured/heavily obscured (specify if due to glare/bubbles/debris)\n"
                       "Overall: good/fair/poor]\n\n"
                       "If this is NOT a valid endoscopic image but contains text/slides about surgical procedures or endoscopic knowledge:\n"
                       "Output should begin with 'PureText:' followed by the main educational content about surgical techniques, anatomical descriptions, or procedural steps\n\n"
                       "If this is neither an endoscopic image nor text/slides:\n"
                       "Output EXACTLY this single line: 'No valid endoscopic image detected'\n\n"
                       "DO NOT include any other text, explanations, or descriptions beyond these formats.",
                       help='Custom prompt for analysis')

    args = parser.parse_args()

    # Initialize the analyzer
    analyzer = ImageAnalyzer()

    # Check if input is a file or directory
    if os.path.isfile(args.input):
        # Single file analysis
        result = analyzer.analyze_local_image(args.input, prompt=args.prompt)
        print("\nAnalysis result:")
        print(result)
    else:
        # Directory analysis
        results = analyzer.analyze_folder(
            folder_path=args.input,
            prompt=args.prompt,
            output_dir=args.output_dir,
            save_results=True,
            sampling=args.sampling
        )

if __name__ == "__main__":
    main()