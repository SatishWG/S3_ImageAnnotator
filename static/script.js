// This file contains the JavaScript code for the front-end functionality of the image annotator app.

const uploadForm = document.getElementById('upload-form');
const annotateForm = document.getElementById('annotate-form');
const fileInput = document.getElementById('file-input');
const objectsInput = document.getElementById('objects-input');
const uploadedImage = document.getElementById('uploaded-image');
const resultsDiv = document.getElementById('results');

let imageUrl = '';

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
            resultsDiv.innerText = 'Error: ' + data.error;
        } else {
            imageUrl = data.image_url;
            uploadedImage.src = imageUrl;
            uploadedImage.style.display = 'block';
            annotateForm.style.display = 'block';
            resultsDiv.innerText = '';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        resultsDiv.innerText = 'An error occurred during upload.';
    });
});

annotateForm.addEventListener('submit', function (e) {
    e.preventDefault();
    
    const objects = objectsInput.value.split(',').map(obj => obj.trim()).filter(obj => obj);
    
    if (objects.length === 0) {
        resultsDiv.innerText = 'Please enter at least one object to detect.';
        return;
    }

    resultsDiv.innerText = 'Processing...';

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
            resultsDiv.innerText = 'Error: ' + data.error;
        } else if (data.warning) {
            resultsDiv.innerHTML = `Warning: ${data.warning}`;
        } else {
            let resultHtml = '<h3>Detected Objects:</h3>';
            for (const [label, instances] of Object.entries(data.detected_objects)) {
                resultHtml += `<p><strong>${label}</strong>:<br>`;
                instances.forEach((coords, index) => {
                    resultHtml += `Instance ${index + 1}: Top-left (${coords[0][0]}, ${coords[0][1]}), ` +
                                `Bottom-right (${coords[1][0]}, ${coords[1][1]})<br>`;
                });
                resultHtml += '</p>';
            }
            resultsDiv.innerHTML = resultHtml;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        resultsDiv.innerText = 'An error occurred during annotation.';
    });
});