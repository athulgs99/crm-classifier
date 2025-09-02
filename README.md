# ServiceNow Ticket Summarizer + Auto-Responder Agent

An AI-powered tool that processes GitHub issues as support tickets, providing intelligent summarization, response generation, and SLA tracking.

## Features

- **GitHub Integration**: Fetches real issues from public repositories
- **AI Summarization**: Uses OpenAI GPT-4 or Anthropic Claude to summarize tickets
- **Auto-Response Generation**: Creates professional yet friendly responses
- **SLA Tracking**: Monitors response times and alerts managers on breaches
- **Session History**: Tracks all processed tickets in the current session
- **Web Interface**: Modern, responsive dashboard built with FastAPI and Tailwind CSS
- **Comprehensive Validation**: Handles edge cases including missing fields, wrong data types, oversized payloads, and duplicate requests

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# LLM Configuration (Choose one)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Email Configuration for SLA Alerts (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
MANAGER_EMAIL=manager@company.com

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
```

### 3. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`

## Usage

1. **Load Recent Tickets**: Click "Load Recent Tickets" to fetch recent GitHub issues
2. **Select a Ticket**: Choose from the dropdown or enter a specific ticket number
3. **Process Ticket**: Click "Process" to generate summary and response
4. **Review Results**: View AI-generated summary, SLA status, and response
5. **Track History**: Monitor all processed tickets in the session

## SLA Configuration

The system tracks SLA compliance based on priority:

- **P1 (Critical)**: 2 hours
- **P2 (High)**: 4 hours
- **P3 (Medium)**: 24 hours
- **P4 (Low)**: 48 hours

When SLA is breached, an email alert is sent to the configured manager.

## API Endpoints

- `GET /` - Main dashboard
- `GET /api/tickets` - Fetch recent tickets
- `GET /api/ticket/{number}` - Get specific ticket
- `POST /api/process-ticket` - Process ticket with AI
- `GET /api/history` - Get session history
- `GET /api/statistics` - Get processing statistics
- `GET /api/validation/status` - Get validation configuration and processed tickets
- `POST /api/validation/clear-processed` - Clear processed tickets list

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + Tailwind CSS + JavaScript
- **LLM**: OpenAI GPT-4 or Anthropic Claude
- **Data Source**: GitHub Issues API
- **Email**: SMTP for SLA alerts

## Customization

- **GitHub Repository**: Change `GITHUB_REPO` in `config.py`
- **SLA Thresholds**: Modify `SLA_THRESHOLDS` in `config.py`
- **Response Templates**: Edit prompts in `llm/responder.py`
- **UI Styling**: Modify templates in `templates/` directory

## Edge Case Handling

The application now includes comprehensive validation to handle common edge cases:

### **Missing Required Fields**
- Validates all required fields (number, title, description, created_time, state)
- Returns detailed error messages for missing or empty fields
- HTTP 422 status code for validation failures

### **Wrong Data Types**
- Converts string numbers to integers automatically
- Validates field types and formats
- Handles malformed JSON gracefully
- Returns specific error messages for type mismatches

### **Oversized Payloads**
- Limits description length to 10,000 characters
- Limits title length to 200 characters
- Limits comments count to 1,000
- Limits labels count to 20
- Automatically truncates oversized content

### **Duplicate Requests**
- Tracks processed ticket IDs in session
- Prevents duplicate processing of the same ticket
- Returns HTTP 409 status code for duplicate requests
- Provides endpoint to clear processed tickets list

### **Testing Edge Cases**
Run the test script to see edge case handling in action:
```bash
python test_edge_cases.py
```

## Troubleshooting

- **API Key Issues**: Ensure your LLM API key is correctly configured
- **GitHub Rate Limits**: The app uses public GitHub API (no authentication required)
- **Email Alerts**: Configure SMTP settings for SLA breach notifications
- **Validation Errors**: Check the validation status endpoint for configuration details

## License

MIT License - feel free to use and modify as needed.
