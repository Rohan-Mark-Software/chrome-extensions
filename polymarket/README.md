# Project Name

## Getting Started

### Chrome Extension Setup

1. Navigate to the chrome extension folder:

   ```bash
   cd chrome-extension
   ```

2. Run the auto-reload script:
   ```bash
   node auto-reload.js
   ```

This runs the Puppeteer application to automatically reload the extension, eliminating the need to manually reload the unpacked version in Chrome.

### Polymarket Backend Setup

#### Prerequisites

- [Ollama](https://ollama.ai/) installed on your system
- Python 3.x

#### Installation & Running

1. **Start the Ollama server** with Chrome extension CORS support:

   ```bash
   OLLAMA_ORIGINS=chrome-extension://* ollama serve
   ```

2. **Install Python dependencies:**

   ```bash
   pip3 install -r requirements.txt
   ```

   _Note: If you don't have a requirements.txt file, install dependencies individually as needed._

3. **Run the search script:**
   ```bash
   python3 app.py
   ```
