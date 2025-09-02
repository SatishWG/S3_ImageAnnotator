from flask import Flask, request, render_template, jsonify, url_for
import os
from werkzeug.utils import secure_filename
from objectSegmentation import extract_segmentation_masks
import json
from PIL import Image
import shutil

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
        # Get original image dimensions
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            print(f"Original image dimensions: {img.size}")

        # Create segmentation output directory
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'segmentation')
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract segmentation masks with original dimensions
        extract_segmentation_masks(image_path, output_dir)
        
        # Process results
        detected_objects = {}
        clean_objects = [obj.strip().lower() for obj in objects]
        
        # Look for mask files
        mask_files = [f for f in os.listdir(output_dir) if f.endswith('_mask.png')]
        
        for filename in mask_files:
            label = filename.split('_')[0].lower()
            
            if any(obj in label for obj in clean_objects):
                original_label = filename.split('_')[0]
                mask_path = os.path.join(output_dir, filename)
                
                with Image.open(mask_path) as mask:
                    bbox = mask.getbbox()  # Returns (left, top, right, bottom)
                    if bbox:
                        if original_label not in detected_objects:
                            detected_objects[original_label] = []
                        
                        detected_objects[original_label].append([
                            (bbox[0], bbox[1]),  # Original top-left coordinates
                            (bbox[2], bbox[3])   # Original bottom-right coordinates
                        ])
        
        return detected_objects
    
    except Exception as e:
        print(f"Error in process_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def cleanup_directories():
    """Clean up segmentation and uploads directories"""
    try:
        # Clean segmentation directory
        segmentation_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'segmentation')
        if os.path.exists(segmentation_dir):
            shutil.rmtree(segmentation_dir)
            os.makedirs(segmentation_dir)

        # Clean uploads directory except segmentation folder
        uploads_dir = app.config['UPLOAD_FOLDER']
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            if item != 'segmentation' and os.path.isfile(item_path):
                os.remove(item_path)

    except Exception as e:
        print(f"Error cleaning directories: {e}")

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
        # Clean up before uploading new image
        cleanup_directories()
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({'image_url': url_for('static', filename=f'uploads/{filename}')})

    return jsonify({'error': 'File type not allowed'})

@app.route('/annotate', methods=['POST'])
def annotate():
    try:
        data = request.json
        objects = data.get('objects', [])
        image_url = data.get('image_url', '')
        
        print(f"Annotating image: {image_url}")
        print(f"Looking for objects: {objects}")
        
        # Convert URL to file path
        image_path = os.path.join(app.root_path, image_url.lstrip('/'))
        
        if not os.path.exists(image_path):
            print(f"Image not found at path: {image_path}")
            return jsonify({'error': 'Image not found'})
        
        # Process image with Gemini 2.0 Flash
        detected_objects = process_image(image_path, objects)
        
        if not detected_objects:
            print("No objects detected")
            return jsonify({'warning': 'No objects detected', 'detected_objects': {}})
            
        return jsonify({'detected_objects': detected_objects})
        
    except Exception as e:
        print(f"Error in annotate route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)