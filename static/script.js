// This file contains the JavaScript code for the front-end functionality of the image annotator app.

document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('file-input');
    const objectsInput = document.getElementById('objects-input');
    const file = fileInput.files[0];
    const objects = objectsInput.value;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('objects', objects);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('results').innerText = 'Error: ' + data.error;
        } else {
            // Display the uploaded image
            const imagePath = 'uploads/' + data.filename;
            document.getElementById('uploaded-image').src = imagePath;
            document.getElementById('uploaded-image').style.display = 'block'; // Make sure the image is visible

            // Display detected objects (for demonstration)
            let resultsText = 'Detected Objects:<br>';
            for (const obj in data.detected_objects) {
                resultsText += `${obj}: ${data.detected_objects[obj]}<br>`;
            }
            document.getElementById('results').innerHTML = resultsText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('results').innerText = 'An error occurred.';
    });
});