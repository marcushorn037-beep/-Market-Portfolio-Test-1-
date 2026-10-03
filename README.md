# Canadian Market Portfolio Tracker

A web-based portfolio tracker for Canadian investors to monitor stocks, ETFs, and bonds on Canadian exchanges (TSX, TSX-V, TSXH).

## Features

- **Portfolio Management**: Add, edit, and delete holdings
- **Real-time Quotes**: Track prices for Canadian securities (TSX-listed)
- **Performance Tracking**: Monitor gains/losses and portfolio performance
- **Sector Analysis**: View portfolio composition by sector
- **Currency Support**: CAD and USD currency tracking
- **Cost Basis Tracking**: Monitor ACB (Average Cost Base) for tax purposes
- **Dividend Tracking**: Track dividend income
- **Export Reports**: Generate CSV reports for tax reporting

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla or Vue.js)
- **Backend**: Python/Flask or Node.js/Express
- **Database**: SQLite or PostgreSQL
- **API Integration**: Alpha Vantage, Finnhub, or TMRX API for TSX quotes

## Getting Started

### Prerequisites

- Python 3.8+ or Node.js 14+
- pip or npm package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/marcushorn037-beep/-Market-Portfolio-Test-1-.git
cd -Market-Portfolio-Test-1-

# Install dependencies
pip install -r requirements.txt
# or
npm install
```

### Running the Application

```bash
# Python/Flask
python app.py

# Node.js
npm start
```

Access the application at `http://localhost:5000`

## Project Structure

```
.
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .gitignore
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   ├── index.html
│   ├── portfolio.html
│   └── reports.html
└── database/
    └── schema.sql
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and personal use only. Always consult with a financial advisor before making investment decisions.
