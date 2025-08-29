# Image Annotator App

This is a simple image annotator application built using Flask. Users can upload an image and provide a list of objects to be annotated. The application processes the image to identify the specified objects and returns their coordinates.

## Project Structure

```
image_annotator_app
├── app.py                # Main Flask application file
├── static
│   ├── script.js         # JavaScript for front-end functionality
│   └── style.css         # CSS styles for the application
├── templates
│   └── index.html        # Main HTML file for the application
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Instructions to Run the Application

1. **Install UV Package Manager**: Ensure you have UV installed. If not, follow the installation instructions for UV.

2. **Create a Virtual Environment**: Navigate to your project directory and create a virtual environment using UV:
   ```
   uv create venv
   ```

3. **Activate the Virtual Environment**: Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install Dependencies**: Install the required packages listed in `requirements.txt`:
   ```
   uv install -r requirements.txt
   ```

5. **Run the Flask Application**: Start the Flask server:
   ```
   uv run app.py
   ```

6. **Access the Application**: Open your web browser and go to `http://127.0.0.1:5000` to access the image annotator app.