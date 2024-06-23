from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

#config ENV
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
app.config['SECRET_KEY'] = 'automationperplexity'

#init MySQL
mysql = MySQL(app)

#Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")

ALLOWED_EXTENSIONS = set(['csv', 'pdf'])

def change_extension(filename, new_extension):
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    name, _ = os.path.splitext(filename)
    return name + new_extension

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            name, _ = os.path.splitext(filename)
            return redirect(url_for('upload_pdf', filename=name))
    return render_template('upload_csv.html')

@app.route('/upload_pdf/<filename>', methods=['GET', 'POST'])
def upload_pdf(filename):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            _, ext = os.path.splitext(secure_filename(file.filename))
            changed_filename = change_extension(filename, ext)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], changed_filename))
            return redirect(url_for('uploaded', filename=filename))
    return render_template('upload_pdf.html')

@app.route('/uploaded/<filename>', methods=['GET', 'POST'])
def uploaded(filename):
    return render_template('uploaded.html', filename=filename)

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    filename = data['filename']
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    csv_file_name = filename + ".csv"
    csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_file_name)
    pdf_file_name = filename + ".pdf"
    pdf_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file_name)
    if not ( os.path.exists(csv_file_path) and os.path.exists(pdf_file_path) ):
        return jsonify({"error": "File not found"}), 404
    return jsonify({"csv_file_name": csv_file_name, "pdf_file_name": pdf_file_name}), 200

@app.route('/')
def main_home():
    return render_template('home.html')

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5001)
    except OSError as e:
        print(f"Error: {e}")
        if e.errno == 10038:
            print("Invalid socket operation")