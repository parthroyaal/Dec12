from flask import Flask, request, render_template_string, jsonify
import base64
import requests
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- HTML Templates ---

UPLOAD_SECTION = """
<h2>Upload Image</h2>
<input type="file" id="image-upload" accept="image/*">
<div id="image-container" style="display:none;">
    <img id="display-image" style="max-width:100%;">
</div>
"""

QUERY_SECTION = """
<h2>Ask Question</h2>
<textarea id="query-input" rows="4" placeholder="Enter your question about the image"></textarea>
<button id="submit-query">Submit Query</button>
"""

RESPONSE_SECTION = """
<div id="response-container-{model}" style="display:none;">
    <h2>{model} Response</h2>
    <div id="response-text-{model}"></div>
</div>
"""  # Formatted with model name

ERROR_SECTION = """
<div id="error-container" style="display:none;">
    <p id="error-text" style="color:red;"></p>
</div>
"""

JAVASCRIPT_SECTION = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const imageUpload = document.getElementById('image-upload');
        const displayImage = document.getElementById('display-image');
        const imageContainer = document.getElementById('image-container');
        const queryInput = document.getElementById('query-input');
        const submitQuery = document.getElementById('submit-query');
        const errorContainer = document.getElementById('error-container');
        const errorText = document.getElementById('error-text');

        imageUpload.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    displayImage.src = e.target.result;
                    imageContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        submitQuery.addEventListener('click', async () => {
            const image = imageUpload.files[0];
            const query = queryInput.value;

            if (!image || !query) {
                showError('Please upload an image and enter a query.');
                return;
            }

            const formData = new FormData();
            formData.append('image', image);
            formData.append('query', query);

            try {
                submitQuery.disabled = true;
                submitQuery.textContent = 'Processing...';

                const response = await fetch('/upload_and_query', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || 'An error occurred');
                }

                ['llama', 'llava'].forEach(model => {
                    const responseContainer = document.getElementById(`response-container-${model}`);
                    const responseText = document.getElementById(`response-text-${model}`);
                    responseText.innerHTML = marked.parse(result[model]);
                    responseContainer.style.display = 'block';
                });

                errorContainer.style.display = 'none';

            } catch (error) {
                showError(error.message);
            } finally {
                submitQuery.disabled = false;
                submitQuery.textContent = 'Submit Query';
            }
        });

        function showError(message) {
            errorText.textContent = message;
            errorContainer.style.display = 'block';
            ['llama', 'llava'].forEach(model => {
                const responseContainer = document.getElementById(`response-container-${model}`);
                responseContainer.style.display = 'none';
            });
        }
    });
</script>
"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Analyze Image Application</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
    <h1>ANALYZE IMAGE APPLICATION</h1>
    <div>{UPLOAD_SECTION}</div>
    <div>{QUERY_SECTION}</div>
    {RESPONSE_SECTION.format(model="llama")}
    {RESPONSE_SECTION.format(model="llava")}
    {ERROR_SECTION}
    {JAVASCRIPT_SECTION}
</body>
</html>
"""

# --- Helper Functions ---

def encode_image(image_content):
    return base64.b64encode(image_content).decode('utf-8')

def validate_image(image_content):
    try:
        Image.open(io.BytesIO(image_content)).verify()
        return True
    except Exception as e:
        return str(e)

def make_api_request(model, messages):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 1000  # Or adjust as needed
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30 # Increase if necessary for larger images/responses
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error from API: {e}"


def process_image_and_query(image_content, query):
    encoded_image = encode_image(image_content)
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": query},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
        ]
    }]

    responses = {}
    for model_name, model in [
        ("llama", "llama-3.2-11b-vision-preview"),  # Update if using different models
        ("llava", "llava-v1.5-7b-4096-preview")   # Update if using different models
    ]:
        responses[model_name] = make_api_request(model, messages)
    return responses


# --- Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload_and_query', methods=['POST'])
def upload_and_query():
    image_file = request.files.get('image')
    query = request.form.get('query')

    if not image_file or not query:
        return jsonify({'detail': 'Missing image or query'}), 400

    image_content = image_file.read()
    if not image_content:
         return jsonify({'detail': 'Empty file'}), 400
    

    validation_result = validate_image(image_content)
    if isinstance(validation_result, str):  # Validation failed
        return jsonify({'detail': f'Invalid image format: {validation_result}'}), 400


    try:
        responses = process_image_and_query(image_content, query)
        return jsonify(responses)
    except Exception as e:
        return jsonify({'detail': str(e)}), 500



if __name__ == '__main__':
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in the .env file")
    app.run(host='0.0.0.0', port=8000, debug=True)