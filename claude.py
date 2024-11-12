import os
import base64
from anthropic import Anthropic
from utils.key_loader import load_api_keys

# Load encrypted keys
api_keys = load_api_keys()
anthropic_key = api_keys['ANTHROPIC_API_KEY']


def encode_image_to_base64(image_path):
	"""
	Encode an image file to base64 string
	"""
	with open(image_path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image(image_path, prompt):
	"""
	Analyze an image using Claude's vision capabilities
	"""
	# Initialize the Anthropic client with API key
	client = Anthropic(
		api_key=anthropic_key  # Replace with your actual API key
	)

	# Encode image to base64
	base64_image = encode_image_to_base64(image_path)

	# Create the message with the image
	message = client.messages.create(
		model="claude-3-opus-20240229",  # or "claude-3-sonnet-20240229"
		max_tokens=1024,
		messages=[{
			"role": "user",
			"content": [
				{
					"type": "image",
					"source": {
						"type": "base64",
						"media_type": "image/jpeg",  # adjust based on your image type
						"data": base64_image
					}
				},
				{
					"type": "text",
					"text": prompt
				}
			]
		}]
	)

	return message.content[0].text  # Access the text content of the response


# Example usage
if __name__ == "__main__":
	# Example: Analyze an image
	image_path = "/data/jj/proj/EndoGPT/test_frames/frame_20.jpg"
	prompt = "Please describe what you see in this image in detail."

	try:
		# Set your API key as an environment variable
		os.environ["ANTHROPIC_API_KEY"] = anthropic_key  # Replace with your actual API key

		response = analyze_image(image_path, prompt)
		print("Claude's Analysis:")
		print(response)
	except Exception as e:
		print(f"An error occurred: {e}")