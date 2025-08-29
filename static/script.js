// This file contains the JavaScript code for the front-end functionality of the image annotator app.

document.getElementById('uploadForm').onsubmit = function(event) {
    event.preventDefault(); // Prevent the form from submitting the default way

    const formData = new FormData();
    const imageFile = document.getElementById('imageInput').files[0];
    const objectList = document.getElementById('objectInput').value;

    formData.append('image', imageFile);
    formData.append('objects', objectList);

    fetch('/annotate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('result');
        resultDiv.innerHTML = ''; // Clear previous results

        if (data.success) {
            data.coordinates.forEach(coord => {
                const coordElement = document.createElement('div');
                coordElement.textContent = `Object: ${coord.object}, Coordinates: ${coord.coordinates}`;
                resultDiv.appendChild(coordElement);
            });
        } else {
            resultDiv.textContent = 'Error: ' + data.message;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
};