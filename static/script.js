// This file contains the JavaScript code for the front-end functionality of the image annotator app.

const uploadForm = document.getElementById('upload-form');
const annotateForm = document.getElementById('annotate-form');
const fileInput = document.getElementById('file-input');
const objectsInput = document.getElementById('objects-input');
const uploadedImage = document.getElementById('uploaded-image');
const annotationCanvas = document.getElementById('annotation-canvas');
const annotationsPanel = document.getElementById('annotations-panel');

let imageUrl = '';

function drawBoundingBoxes(detectedObjects) {
    const canvas = annotationCanvas;
    const ctx = canvas.getContext('2d');
    
    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set canvas size to match image
    canvas.width = uploadedImage.width;
    canvas.height = uploadedImage.height;
    
    // Draw bounding boxes
    Object.entries(detectedObjects).forEach(([label, instances]) => {
        // Generate a random color for this object type
        const hue = Math.random() * 360;
        ctx.strokeStyle = `hsl(${hue}, 70%, 50%)`;
        ctx.lineWidth = 2;
        ctx.font = '16px Arial';
        ctx.fillStyle = ctx.strokeStyle;
        
        instances.forEach((coords, index) => {
            const [topLeft, bottomRight] = coords;
            const width = bottomRight[0] - topLeft[0];
            const height = bottomRight[1] - topLeft[1];
            
            // Draw rectangle
            ctx.strokeRect(topLeft[0], topLeft[1], width, height);
            
            // Draw label
            ctx.fillText(`${label} ${index + 1}`, topLeft[0], topLeft[1] - 5);
        });
    });
}

function updateAnnotationsPanel(detectedObjects) {
    let html = '<h3>Detected Objects</h3>';
    
    Object.entries(detectedObjects).forEach(([label, instances]) => {
        html += `<div class="annotation-item">
            <strong>${label}</strong> (${instances.length} found)<br>`;
        
        instances.forEach((coords, index) => {
            const [topLeft, bottomRight] = coords;
            html += `<div style="margin-left: 10px;">
                Instance ${index + 1}:<br>
                Top-left: (${topLeft[0]}, ${topLeft[1]})<br>
                Bottom-right: (${bottomRight[0]}, ${bottomRight[1]})
            </div>`;
        });
        
        html += '</div>';
    });
    
    annotationsPanel.innerHTML = html;
}

uploadForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            annotationsPanel.innerText = 'Error: ' + data.error;
        } else {
            imageUrl = data.image_url;
            uploadedImage.src = imageUrl;
            uploadedImage.style.display = 'block';
            annotateForm.style.display = 'block';
            annotationsPanel.innerText = '';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        annotationsPanel.innerText = 'An error occurred during upload.';
    });
});

annotateForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    const objects = objectsInput.value.split(',').map(obj => obj.trim()).filter(obj => obj);
    
    if (objects.length === 0) {
        annotationsPanel.innerText = 'Please enter at least one object to detect.';
        return;
    }
    
    annotationsPanel.innerText = 'Processing...';
    
    fetch('/annotate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ objects, image_url: imageUrl })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            annotationsPanel.innerText = 'Error: ' + data.error;
        } else if (data.warning) {
            annotationsPanel.innerHTML = `Warning: ${data.warning}`;
        } else {
            drawBoundingBoxes(data.detected_objects);
            updateAnnotationsPanel(data.detected_objects);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        annotationsPanel.innerText = 'An error occurred during annotation.';
    });
});