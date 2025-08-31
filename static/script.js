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

                // Display the uploaded image
                uploadedImage.src = imageUrl;
                uploadedImage.style.display = 'block';

                // Show the annotate form
                annotateForm.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerText = 'An error occurred.';
        });
});

annotateForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const objects = objectsInput.value.split(',');

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
            } else {
                // Display detected object coordinates
                const detectedObjects = data.detected_objects;
                let resultsText = 'Detected Objects:<br>';
                for (const obj in detectedObjects) {
                    const [start, end] = detectedObjects[obj];
                    resultsText += `${obj}: Start(${start[0]}, ${start[1]}), End(${end[0]}, ${end[1]})<br>`;
                }
                resultsDiv.innerHTML = resultsText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerText = 'An error occurred.';
        });
});