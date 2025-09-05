from flask import Flask, request, render_template, jsonify, url_for
import os
from werkzeug.utils import secure_filename
from objectSegmentation import extract_segmentation_masks
import json
from PIL import Image
import shutil
from collections import defaultdict

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store detected objects per image
app.detected_objects_cache = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def are_coordinates_same(coords1, coords2, tolerance=5):
    """Compare two sets of coordinates with some tolerance"""
    [tl1, br1] = coords1
    [tl2, br2] = coords2
    return (abs(tl1[0] - tl2[0]) <= tolerance and 
            abs(tl1[1] - tl2[1]) <= tolerance and
            abs(br1[0] - br2[0]) <= tolerance and
            abs(br1[1] - br2[1]) <= tolerance)

def remove_duplicate_instances(objects_dict):
    """Remove instances with duplicate coordinates"""
    for label, instances in objects_dict.items():
        if not instances:
            continue
            
        unique_instances = [instances[0]]  # Keep first instance
        
        # Compare against existing unique instances
        for instance in instances[1:]:
            is_duplicate = False
            for unique_instance in unique_instances:
                if are_coordinates_same(instance, unique_instance):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_instances.append(instance)
        
        objects_dict[label] = unique_instances
    
    return objects_dict

def process_image(image_path, objects):
    """Process image using Gemini 2.0 Flash for object detection"""
    try:
        image_key = os.path.basename(image_path)
        clean_objects = [obj.strip().lower() for obj in objects]
        
        # Initialize detected_objects
        detected_objects = {}
        
        # First check cache
        if image_key in app.detected_objects_cache:
            cached_objects = app.detected_objects_cache[image_key]
            
            # Return only currently requested objects from cache
            for label, instances in cached_objects.items():
                if any(obj in label.lower() for obj in clean_objects):
                    detected_objects[label] = instances.copy()  # Make a copy of instances
            
            # If all requested objects are found in cache, return them
            if detected_objects and all(any(obj in label.lower() 
                for label in detected_objects.keys()) for obj in clean_objects):
                return detected_objects

        # Find objects not in cache
        cached_labels = set()
        if image_key in app.detected_objects_cache:
            cached_labels = {label.lower() for label in app.detected_objects_cache[image_key].keys()}
        
        new_objects = [obj for obj in clean_objects 
                      if not any(obj in label for label in cached_labels)]

        if new_objects:
            output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'segmentation')
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract masks for new detection
            extract_segmentation_masks(image_path, output_dir)
            
            # Process new masks
            mask_files = [f for f in os.listdir(output_dir) if f.endswith('_mask.png')]
            new_detected = {}
            
            for filename in mask_files:
                label = filename.split('_')[0].lower()
                
                if any(obj in label for obj in new_objects):
                    original_label = filename.split('_')[0]
                    mask_path = os.path.join(output_dir, filename)
                    
                    with Image.open(mask_path) as mask:
                        bbox = mask.getbbox()
                        if bbox:
                            if original_label not in new_detected:
                                new_detected[original_label] = []
                            new_detected[original_label].append(
                                [(bbox[0], bbox[1]), (bbox[2], bbox[3])]
                            )
            
            # Update cache with new detections
            if image_key not in app.detected_objects_cache:
                app.detected_objects_cache[image_key] = {}
            app.detected_objects_cache[image_key].update(new_detected)
            
            # Merge new detections with cached ones
            detected_objects.update(new_detected)
        
        # Before returning detected_objects, remove duplicates
        detected_objects = remove_duplicate_instances(detected_objects)
        return detected_objects
                
    except Exception as e:
        print(f"Error in process_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def cleanup_directories():
    """Clean up segmentation and uploads directories"""
    try:
        # Clear the objects cache when cleaning up
        app.detected_objects_cache.clear()
        
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
        # Clear the objects cache for the new image
        app.detected_objects_cache.clear()
        
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