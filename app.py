from flask import Flask, request, render_template, jsonify, url_for
import os
from werkzeug.utils import secure_filename

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
    # Dummy implementation for object detection
    detected_objects = {}
    for obj in objects:
        detected_objects[obj] = [(50, 50), (150, 150)]  # Dummy coordinates
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

        # Return the image URL
        return jsonify({'image_url': url_for('static', filename=f'uploads/{filename}')})

    return jsonify({'error': 'File type not allowed'})

@app.route('/annotate', methods=['POST'])
def annotate():
    data = request.json
    objects = data.get('objects', [])
    image_url = data.get('image_url', '')

    # Dummy annotations
    detected_objects = process_image(image_url, objects)

    return jsonify({'detected_objects': detected_objects})

if __name__ == '__main__':
    app.run(debug=True)