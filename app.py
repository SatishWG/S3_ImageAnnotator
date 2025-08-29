from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path, objects):
    # Dummy implementation for object detection
    # In a real application, you would use a model to detect objects
    detected_objects = {}
    for obj in objects:
        detected_objects[obj] = [(50, 50), (100, 100)]  # Dummy coordinates
    return detected_objects

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

        objects = request.form.get('objects').split(',')
        detected_objects = process_image(file_path, objects)

        # Return the filename to display the image
        return jsonify({'filename': filename, 'detected_objects': detected_objects})

    return jsonify({'error': 'File type not allowed'})

if __name__ == '__main__':
    app.run(debug=True)