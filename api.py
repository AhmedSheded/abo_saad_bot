from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from processing import process_data
app = Flask(__name__)

# Directory to store uploaded and processed files
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure the folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/process', methods=['POST'])
def process():
    # Extract form data
    template = request.form.get('template')
    language = request.form.get('language')
    text = request.form.get('text')

    # Extract photo files
    files = request.files.getlist('photos')
    photo_paths = []

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_paths.append(file_path)

    # Call the process_data function
    processed_image_path = process_data(template, language, text, photo_paths)

    # Return the path to the processed image as a response
    return jsonify({'processed_image_path': processed_image_path})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
