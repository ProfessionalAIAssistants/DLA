# DLA CRM System

A comprehensive Customer Relationship Management system for Defense Logistics Agency operations.

## Project Structure

```
DLA/
├── app.py                 # Main application entry point
├── crm_app.py            # Flask application with routes and API endpoints
├── mfr_parser.py         # Manufacturer string parsing utility
├── config/               # Configuration files
├── data/                 # Database and data files
├── docs/                 # Documentation
├── Layout/               # UI/Layout specifications
├── logs/                 # Application logs
├── scripts/              # Utility scripts
├── src/                  # Source code modules
│   ├── core/            # Core business logic
│   ├── email_automation/ # Email processing
│   └── pdf/             # PDF processing
├── tests/                # Test files and debugging utilities
└── web/                  # Web interface (templates, static files)
    ├── static/          # CSS, JS, images
    └── templates/       # Jinja2 HTML templates
```

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r docs/requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access Interface**
   Open http://localhost:5000 in your browser

## Key Features

- **Contact Management** - Track contacts and their relationships
- **Account Management** - Manage customer and vendor accounts
- **Opportunity Tracking** - Sales pipeline management
- **QPL Management** - Qualified Products List integration
- **PDF Processing** - Automated document processing
- **Email Automation** - Automated email workflows
- **Task Management** - Project and task tracking

## Development

- **Tests**: See `tests/README.md` for testing utilities
- **Documentation**: Detailed docs in `docs/` directory
- **Scripts**: Utility scripts in `scripts/` directory

## Support

For issues and feature requests, refer to the documentation in the `docs/` directory.
