from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads and interact with the backend
@app.route('/transform', methods=['POST'])
def transform():
    input_xml = request.form['inputXML']
    xsl_transformation = request.form['xslFile']  # Ensure this contains the actual XSLT content
    
    # Send the files to your Node.js backend
    response = requests.post('http://backend:3000/transform', json={
        'inputXML': input_xml,
        'xslTransformation': xsl_transformation
    })

    # Return the transformed XML result
    return jsonify({'output': response.text})  # Return wrapped in a key

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

