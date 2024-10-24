# gmgn-price-tracker

An automated web scraper that fetches token prices from gmgn.ai and updates them to Google Sheets. Built with Python, Playwright, and Google Sheets API.

## Features

- Asynchronous web scraping with Playwright
- Google Sheets integration for data storage
- Configurable concurrent tasks
- Automatic retry mechanism
- Detailed logging
- Random user agent rotation for better scraping reliability
- Screenshot capture for debugging

## Prerequisites

- Python 3.7+
- Google Cloud Project with Sheets API enabled
- Google Service Account with appropriate permissions
- Access to gmgn.ai

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gmgn-price-tracker.git
cd gmgn-price-tracker
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables in a `.env` file:
```env
GOOGLE_SHEETS_SCOPES=https://www.googleapis.com/auth/spreadsheets
SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_KEY=path/to/your/service-account-key.json
MAX_CONCURRENT_TASKS=5
SHEET_NAME=General
START_ROW=142
SLEEP_INTERVAL=60
SCREENSHOT_PATH=last.jpg
```

## Google Sheets Setup

1. Create a Google Cloud Project
2. Enable the Google Sheets API
3. Create a service account and download the JSON key file
4. Share your Google Sheet with the service account email
5. Ensure your spreadsheet has the following columns:
   - Column A: Token Network
   - Column B: Token Address
   - Column E: Price (will be updated by the script)
   - Column F: Website URL (will be updated by the script)
   - Column T: Last Update Date (will be updated by the script)

## Usage

Run the script:
```bash
python3 main.py
```

The script will:
1. Read token data from your Google Sheet starting from the configured row
2. Fetch current prices from gmgn.ai
3. Update the sheet with new prices, URLs, and timestamps
4. Sleep for the configured interval before the next update cycle

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| GOOGLE_SHEETS_SCOPES | Google Sheets API scope | https://www.googleapis.com/auth/spreadsheets |
| SPREADSHEET_ID | ID of your Google Sheet | Required |
| GOOGLE_SERVICE_ACCOUNT_KEY | Path to service account key file | Required |
| MAX_CONCURRENT_TASKS | Maximum number of concurrent scraping tasks | 5 |
| SHEET_NAME | Name of the sheet to read/write | General |
| START_ROW | First row to process | 142 |
| SLEEP_INTERVAL | Time to wait between update cycles (seconds) | 60 |
| SCREENSHOT_PATH | Path to save debug screenshots | last.jpg |

## Logging

The script logs all activities to `logging.log`. Each log entry includes:
- Timestamp
- Log level
- Action performed
- Any errors or warnings

## Error Handling

The script includes comprehensive error handling for:
- Network issues
- Invalid token addresses
- Google Sheets API errors
- Web scraping failures

Screenshots are automatically captured for debugging purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)