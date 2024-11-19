from PIL import Image, ImageDraw, ImageFont
import os
import glob
import argparse

def concat_images_single_folder(input_folder, output_folder):
    """Process a single folder to concatenate images in 1x4 grid"""
    # Get all image files in the folder
    image_files = sorted(glob.glob(os.path.join(input_folder, "*.jpg")) + 
                        glob.glob(os.path.join(input_folder, "*.png")))
    
    # Process images in groups of 4
    for i in range(0, len(image_files), 4):
        group = image_files[i:i+4]
        
        # Skip if we don't have a full group of 4 images
        if len(group) < 4:
            continue
            
        # Open and resize all images to the same size
        images = [Image.open(img) for img in group]
        min_height = min(img.size[1] for img in images)
        min_width = min(img.size[0] for img in images)
        
        # Resize images to maintain aspect ratio
        images = [img.resize((min_width, min_height), Image.Resampling.LANCZOS) 
                 for img in images]
        
        # Create output image (1x4 grid)
        output = Image.new('RGB', (min_width * 4, min_height))
        
        # Paste images and add numbers
        for idx, img in enumerate(images):
            # Calculate position (now just horizontal)
            x = idx * min_width
            y = 0
            
            # Paste image
            output.paste(img, (x, y))
            
            # Add number with blue circle background
            draw = ImageDraw.Draw(output)
            font_size = min(min_width, min_height) // 10  # Increased from 20 to 10
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size for circle
            text = str(idx + 1)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate circle position and size
            circle_padding = font_size // 3
            circle_x = x + 20
            circle_y = y + 20
            circle_radius = max(text_width, text_height) // 2 + circle_padding
            
            # Draw blue circle
            draw.ellipse([circle_x - circle_radius, circle_y - circle_radius,
                         circle_x + circle_radius, circle_y + circle_radius],
                        fill='blue')
            
            # Draw number
            draw.text((circle_x - text_width//2, circle_y - text_height//2), 
                     text, fill='white', font=font)
        
        # Save the concatenated image
        # Get base filenames without extensions
        filenames = [os.path.splitext(os.path.basename(img))[0] for img in group]
        output_filename = '-'.join(filenames) + '.jpg'
        output_path = os.path.join(output_folder, output_filename)
        output.save(output_path, quality=95)

def process_folder_structure(parent_dir):
    """Process the entire folder structure"""
    # Loop through each main folder in the parent directory
    for main_folder in os.listdir(parent_dir):
        main_path = os.path.join(parent_dir, main_folder)
        if os.path.isdir(main_path):
            # Loop through each subfolder
            for subfolder in os.listdir(main_path):
                subfolder_path = os.path.join(main_path, subfolder)
                if os.path.isdir(subfolder_path):
                    # Create output folder path
                    output_folder = os.path.join(subfolder_path, "concatenated_images")
                    
                    # Create output directory if it doesn't exist
                    os.makedirs(output_folder, exist_ok=True)
                    
                    print(f"Processing subfolder: {subfolder_path}")
                    # Process images in this subfolder
                    concat_images_single_folder(subfolder_path, output_folder)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Concatenate images in 1x4 grid')
    parser.add_argument('--single', '-s', type=str, help='Path to single folder for processing')
    parser.add_argument('--full', '-f', type=str, help='Path to parent directory for full structure processing')
    
    args = parser.parse_args()
    
    if args.single:
        # Process single folder
        print(f"Processing single folder: {args.single}")
        output_folder = os.path.join(args.single, "concatenated_images")
        os.makedirs(output_folder, exist_ok=True)
        concat_images_single_folder(args.single, output_folder)
        print("Single folder processing complete!")
        
    elif args.full:
        # Process full structure
        print(f"Processing full folder structure from: {args.full}")
        process_folder_structure(args.full)
        print("Full structure processing complete!")
        
    else:
        parser.print_help()
        print("\nError: Please provide either --single or --full argument")

if __name__ == "__main__":
    main() 