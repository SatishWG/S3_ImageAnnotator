// This file contains the JavaScript code for the front-end functionality of the image annotator app.

const uploadForm = document.getElementById('upload-form');
const annotateForm = document.getElementById('annotate-form');
const fileInput = document.getElementById('file-input');
const objectsInput = document.getElementById('objects-input');
const uploadedImage = document.getElementById('uploaded-image');
const annotationCanvas = document.getElementById('annotation-canvas');
const annotationsPanel = document.getElementById('annotations-panel');

let imageUrl = '';
let lastAnnotationObjects = new Set();

function drawBoundingBoxes(detectedObjects) {
    const canvas = annotationCanvas;
    const ctx = canvas.getContext('2d');
    
    // Get the original image dimensions
    const originalWidth = uploadedImage.naturalWidth;
    const originalHeight = uploadedImage.naturalHeight;
    
    // Get the displayed image dimensions
    const displayWidth = uploadedImage.offsetWidth;
    const displayHeight = uploadedImage.offsetHeight;
    
    // Set canvas size to match displayed image size
    canvas.width = displayWidth;
    canvas.height = displayHeight;
    
    // Calculate scaling factors
    const scaleX = displayWidth / originalWidth;
    const scaleY = displayHeight / originalHeight;
    
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
            
            // Scale coordinates to match displayed image size
            const scaledX = topLeft[0] * scaleX;
            const scaledY = topLeft[1] * scaleY;
            const scaledWidth = (bottomRight[0] - topLeft[0]) * scaleX;
            const scaledHeight = (bottomRight[1] - topLeft[1]) * scaleY;
            
            // Draw rectangle
            ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);
            
            // Draw label
            ctx.fillText(`${label} ${index + 1}`, scaledX, scaledY - 5);
        });
    });
}

// Update the image onload event to redraw boxes when image size changes
uploadedImage.onload = function() {
    if (imageUrl) {
        // Wait for next frame to ensure image dimensions are updated
        requestAnimationFrame(() => {
            const data = JSON.parse(annotationsPanel.dataset.lastDetection || '{}');
            if (data.detected_objects) {
                drawBoundingBoxes(data.detected_objects);
            }
        });
    }
};

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

function clearAnnotations() {
    const canvas = annotationCanvas;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    annotationsPanel.innerHTML = '';
    delete annotationsPanel.dataset.lastDetection;
    lastAnnotationObjects.clear();  // Clear the set of annotated objects
}

uploadForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Clear existing annotations before uploading
    clearAnnotations();
    
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
        }
    })
    .catch(error => {
        console.error('Error:', error);
        annotationsPanel.innerText = 'An error occurred during upload.';
    });
});

// Replace the existing annotate form event listener
annotateForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    const objects = objectsInput.value.split(',').map(obj => obj.trim()).filter(obj => obj);
    
    if (objects.length === 0) {
        annotationsPanel.innerText = 'Please enter at least one object to detect.';
        return;
    }
    
    // Always clear previous annotations when starting a new detection
    clearAnnotations();
    
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
            // Store the new detection results
            annotationsPanel.dataset.lastDetection = JSON.stringify(data);
            
            // Update display with only the current detection results
            drawBoundingBoxes(data.detected_objects);
            updateAnnotationsPanel(data.detected_objects);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        annotationsPanel.innerText = 'An error occurred during annotation.';
    });
});