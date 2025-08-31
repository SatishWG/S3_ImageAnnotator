from flask import Flask, request, render_template, jsonify, url_for
import os
from werkzeug.utils import secure_filename
from objectSegmentation import extract_segmentation_masks
import json
from PIL import Image

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path, objects):
    """
    Process image using Gemini 2.0 Flash for object detection
    """
    try:
        # Create a directory for segmentation outputs
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'segmentation')
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract segmentation masks
        extract_segmentation_masks(image_path, output_dir)
        
        # Process the results
        detected_objects = {}
        
        # Get the original image size for coordinate calculation
        with Image.open(image_path) as img:
            img_width, img_height = img.size
        
        # Look for mask files in the output directory
        for filename in os.listdir(output_dir):
            if filename.endswith('_mask.png'):
                # Extract object label from filename
                label = filename.split('_')[0]
                
                # If this object was requested by the user
                if label.lower() in [obj.lower() for obj in objects]:
                    # Get the mask image path
                    mask_path = os.path.join(output_dir, filename)
                    
                    # Open the mask image to get its bounding box
                    with Image.open(mask_path) as mask:
                        bbox = mask.getbbox()  # Returns (left, top, right, bottom)
                        if bbox:
                            # Store coordinates as [(top-left), (bottom-right)]
                            detected_objects[label] = [
                                (bbox[0], bbox[1]),  # top-left
                                (bbox[2], bbox[3])   # bottom-right
                            ]
        
        return detected_objects
    
    except Exception as e:
        print(f"Error in process_image: {str(e)}")
        return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Return the image URL
        return jsonify({'image_url': url_for('static', filename=f'uploads/{filename}')})

    return jsonify({'error': 'File type not allowed'})

@app.route('/annotate', methods=['POST'])
def annotate():
    data = request.json
    objects = data.get('objects', [])
    image_url = data.get('image_url', '')
    
    # Convert URL to file path
    image_path = os.path.join(app.root_path, image_url.lstrip('/'))
    
    # Process image with Gemini 2.0 Flash
    detected_objects = process_image(image_path, objects)
    
    return jsonify({'detected_objects': detected_objects})

if __name__ == '__main__':
    app.run(debug=True)