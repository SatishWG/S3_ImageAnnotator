from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io
import base64
import json
import numpy as np
import os
import load_dotenv

load_dotenv.load_dotenv()  # take environment variables from .env.
os.environ.get('GOOGLE_API_KEY')

client = genai.Client()

def parse_json(json_output: str):
    """Parse JSON output from Gemini model response"""
    try:
        # Find the JSON content between ```json and ```
        start = json_output.find("```json")
        if start != -1:
            # Move past ```json and any whitespace/newline
            json_start = json_output.find('[', start)
            if json_start == -1:
                json_start = json_output.find('{', start)
            
            if json_start != -1:
                # Find the closing ```
                end = json_output.find("```", json_start)
                if end != -1:
                    json_content = json_output[json_start:end].strip()
                    # Parse JSON to validate it
                    json.loads(json_content)  # This will raise an exception if invalid
                    return json_content
        
        # If we couldn't extract valid JSON, try parsing the whole response
        json.loads(json_output)  # This will raise an exception if invalid
        return json_output
        
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw output: {json_output}")
        return "[]"  # Return empty array as fallback

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
    try:
        # Load and resize image
        im = Image.open(image_path)
        im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
        print(f"Image size after thumbnail: {im.size}")

        prompt = """
        Analyze this image and provide segmentation masks for all visible objects.
        Return the results as a JSON array where each object has:
        - "label": descriptive name of the object
        - "box_2d": bounding box coordinates [y0, x0, y1, x1] normalized to 1000x1000
        - "mask": base64 PNG image of the segmentation mask
        Format the response as a valid JSON array only.
        """

        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, im],
            config=config
        )

        # Parse JSON response with improved error handling
        json_str = parse_json(response.text)
        print(f"Parsed JSON string length: {len(json_str)}")
        items = json.loads(json_str)
        print(f"Found {len(items)} objects")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Process each mask
        for i, item in enumerate(items):
            # Get bounding box coordinates
            box = item["box_2d"]
            y0 = int(box[0] / 1000 * im.size[1])
            x0 = int(box[1] / 1000 * im.size[0])
            y1 = int(box[2] / 1000 * im.size[1])
            x1 = int(box[3] / 1000 * im.size[0])

            # Skip invalid boxes
            if y0 >= y1 or x0 >= x1:
                continue

            # Process mask
            png_str = item["mask"]
            if not png_str.startswith("data:image/png;base64,"):
                continue

            # Remove prefix
            png_str = png_str.removeprefix("data:image/png;base64,")
            mask_data = base64.b64decode(png_str)
            mask = Image.open(io.BytesIO(mask_data))

            # Resize mask to match bounding box
            mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

            # Convert mask to numpy array for processing
            mask_array = np.array(mask)

            # Create overlay for this mask
            overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            # Create overlay for the mask
            color = (255, 255, 255, 200)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                        overlay_draw.point((x, y), fill=color)

            # Save individual mask and its overlay
            mask_filename = f"{item['label']}_{i}_mask.png"
            overlay_filename = f"{item['label']}_{i}_overlay.png"

            mask.save(os.path.join(output_dir, mask_filename))

            # Create and save overlay
            composite = Image.alpha_composite(im.convert('RGBA'), overlay)
            composite.save(os.path.join(output_dir, overlay_filename))
            print(f"Saved mask and overlay for {item['label']} to {output_dir}")

    except Exception as e:
        print(f"Error in extract_segmentation_masks: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# Example usage
if __name__ == "__main__":
  extract_segmentation_masks("path/to/image.png")
