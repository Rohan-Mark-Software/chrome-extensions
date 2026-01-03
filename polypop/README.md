# Polypop

## Getting Started

### Prerequisites

Before starting, ensure you have the following installed:

- [Docker](https://www.docker.com/get-started)  
- [Ollama](https://ollama.ai/)  
- Python 3.x  
- Google Chrome  

---

## Chrome Extension Setup

1. **Load the extension in Chrome**:

   - Open Chrome and go to `chrome://extensions/`
   - Enable **Developer mode** (toggle in the top-right corner)
   - Click **Load unpacked** and select the `chrome-extension` folder from this project

2. **Reload after every change**:

   - Whenever you make edits to the extension files, click the **Reload** button on the extension page in Chrome.  
   - This ensures Chrome is using the latest version of your extension.

---

## Polymarket Backend Setup

1. **Start Docker Redis**:

   ```bash
   docker pull redis
   docker run --name redis -p 6379:6379 -d redis
   ```
2. **Start the Ollama server with Chrome extension CORS support**:
   
   ```bash
   OLLAMA_ORIGINS=chrome-extension://* ollama serve
   ```
3. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Run the backend server**:
   ```bash
   python3 app.py
   ```
