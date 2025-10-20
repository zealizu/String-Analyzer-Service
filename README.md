# String Analyzer Service

A Flask-based web service for analyzing and filtering strings. It supports adding strings with computed properties (e.g., palindrome check, length, word count), querying/filtering them via API endpoints, and natural language-based filtering using Google's Gemini AI.

## Features
- **POST /strings**: Add a new string and compute its properties (length, palindrome status, unique characters, word count, SHA256 hash, character frequency).
- **GET /strings**: Retrieve all strings with optional filters (e.g., by palindrome, length, word count, containing character).
- **GET /strings/<value>**: Retrieve a specific string by value.
- **DELETE /strings/<value>**: Delete a specific string by value.
- **GET /strings/filter-by-natural-language?query=<query>**: Filter strings using natural language queries (powered by Gemini AI).

The service stores data in-memory (lost on restart) and uses CORS for cross-origin requests.

## Requirements
- Python 3.8+ (tested with 3.12)
- Google Gemini API key (for NLP filtering endpoint)

## Installation

1. **Clone or Download the Project**:
   ```
   git clone <your-repo-url>
   cd string-analyzer-service
   ```
   (Or simply save the provided `app.py` file in a new directory.)

2. **Create a Virtual Environment** (recommended):
   ```
   python -m venv venv
   ```
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. **Install Dependencies**:
   ```
   pip install flask flask-cors python-dotenv langchain-core langchain-google-genai
   ```
   This installs:
   - `flask`: Web framework.
   - `flask-cors`: Handles CORS.
   - `python-dotenv`: Loads environment variables.
   - `langchain-core` and `langchain-google-genai`: For AI-powered NLP filtering.

## Configuration

1. **Set Up Environment Variables**:
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   - Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
   - The NLP endpoint (`/strings/filter-by-natural-language`) requires this key; other endpoints do not.

2. **Project Structure** (minimal):
   ```
   string-analyzer-service/
   ├── app.py          # Main application file
   ├── .env            # Environment variables (add this)
   └── requirements.txt # Optional: pip freeze > requirements.txt
   ```

## Running the App

1. **Start the Server**:
   ```
   python app.py
   ```
   - The app runs on `http://0.0.0.0:5000` (accessible from localhost or network).
   - Visit `http://localhost:5000/` in your browser to see the welcome message.

2. **Stop the Server**:
   - Press `Ctrl+C` in the terminal.

3. **Production Notes**:
   - For production, use a WSGI server like Gunicorn: `pip install gunicorn` and run `gunicorn -w 4 -b 0.0.0.0:5000 app:app`.
   - Data is in-memory; persist to a database (e.g., SQLite) for durability.

## API Usage Examples

Use tools like `curl`, Postman, or Python `requests` to interact.

### Add a String (POST /strings)
```bash
curl -X POST http://localhost:5000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "racecar"}'
```
Response (201 Created):
```json
{
  "id": "a4d5e2f...sha256_hash",
  "value": "racecar",
  "properties": {
    "length": 7,
    "is_palindrome": true,
    "unique_characters": 4,
    "word_count": 1,
    "sha256_hash": "a4d5e2f...",
    "character_frequency_map": {"r": 2, "a": 2, "c": 2, "e": 1}
  },
  "created_at": "2025-10-20T12:00:00Z"
}
```

### Get All Strings with Filters (GET /strings)
```bash
curl "http://localhost:5000/strings?is_palindrome=true&min_length=5"
```
Response: Filtered JSON array with metadata.

### Get Specific String (GET /strings/<value>)
```bash
curl "http://localhost:5000/strings/racecar"
```

### Delete String (DELETE /strings/<value>)
```bash
curl -X DELETE "http://localhost:5000/strings/racecar"
```

### NLP Filter (GET /strings/filter-by-natural-language)
```bash
curl "http://localhost:5000/strings/filter-by-natural-language?query=palindromic strings longer than 5 characters"
```
- Converts natural language to filters via Gemini AI.
- Example output: Filters for `is_palindrome: true` and `min_length: 6`.

## Error Handling
- 400: Invalid parameters or types.
- 404: String not found.
- 409: Duplicate string.
- 422: NLP query unparseable.

## Troubleshooting
- **No module named 'langchain...'**: Run `pip install` again.
- **API Key Error**: Check `.env` and ensure `load_dotenv()` is called.
- **CORS Issues**: Enabled globally; adjust if needed.
- **In-Memory Data Loss**: Restart clears `string_db`; implement persistence if required.

## Contributing
Fork the repo, make changes, and submit a PR. Tests and docs welcome!
