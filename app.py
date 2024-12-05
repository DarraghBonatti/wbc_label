from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import os
import csv
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Set session to last 7 days

# Store the password securely
PASSWORD = 'your_password'  # Replace with your desired password

# Path to the directory containing images
IMAGE_DIR = 'static/images'
# Path to the file where labels will be stored
LABELS_FILE = 'labels.csv'

# Load images
images = os.listdir(IMAGE_DIR)

# Load existing labels into a dictionary
labels = {}
if os.path.exists(LABELS_FILE):
    with open(LABELS_FILE, 'r') as f:
        reader = csv.reader(f)
        try:
            next(reader)  # Try to skip header
        except StopIteration:
            # File is empty, create it with header
            with open(LABELS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Image Name', 'Label'])
        else:
            # Read the rest of the file
            for row in reader:
                if row:
                    labels[row[0]] = row[1]
else:
    # Create the file with header if it doesn't exist
    with open(LABELS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Image Name', 'Label'])

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    password = request.form['password']
    if password == PASSWORD:
        session['logged_in'] = True
        session.permanent = True  # Make the session permanent
        # Initialize the current_image_index in session if not exists
        if 'current_image_index' not in session:
            session['current_image_index'] = 0
        return redirect(url_for('index'))
    else:
        return "Incorrect password!", 401

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('current_image_index', None)
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Get current_image_index from session
    current_image_index = session.get('current_image_index', 0)

    if 0 <= current_image_index < len(images):
        image_path = os.path.join(IMAGE_DIR, images[current_image_index])
        current_image_name = images[current_image_index]
        return render_template('index.html', 
                             image_path=image_path, 
                             image_name=current_image_name,
                             index=current_image_index, 
                             total=len(images))
    else:
        return "All images labeled!"

@app.route('/label', methods=['POST'])
def label():
    if not session.get('logged_in'):
        return jsonify(success=False, message="Unauthorized"), 401

    current_image_index = session.get('current_image_index', 0)
    data = request.json
    image_name = images[current_image_index]
    label = data['label']

    # Update the label in the dictionary
    labels[image_name] = label

    # Write all labels back to the CSV file
    with open(LABELS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Image Name', 'Label'])
        for img_name, lbl in labels.items():
            writer.writerow([img_name, lbl])

    current_image_index += 1
    session['current_image_index'] = current_image_index
    return jsonify(success=True)

@app.route('/navigate', methods=['POST'])
def navigate():
    if not session.get('logged_in'):
        return jsonify(success=False, message="Unauthorized"), 401

    current_image_index = session.get('current_image_index', 0)
    data = request.json
    direction = data['direction']

    if direction == 'next' and current_image_index < len(images) - 1:
        current_image_index += 1
    elif direction == 'prev' and current_image_index > 0:
        current_image_index -= 1

    session['current_image_index'] = current_image_index
    return jsonify(success=True)

@app.route('/download_labels')
def download_labels():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_file(LABELS_FILE, as_attachment=True)

@app.route('/get_labels')
def get_labels():
    if not session.get('logged_in'):
        return jsonify(success=False, message="Unauthorized"), 401

    # Read the CSV file and return its contents as JSON
    labels_list = []
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    labels_list.append({'image_name': row[0], 'label': row[1]})
    return jsonify(labels_list)

if __name__ == '__main__':
    app.run(debug=True)