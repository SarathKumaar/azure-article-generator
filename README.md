# Azure Article Generator

An Azure Functions-based system that generates comprehensive articles by combining academic research from arXiv and practical insights from Medium articles.

## System Architecture

The system consists of four Azure Functions:
1. Input Handler - Accepts article themes
2. arXiv Scraper - Fetches relevant research papers
3. Medium Scraper - Collects related Medium articles
4. Article Generator - Creates final article using GPT-4

## Prerequisites

- Azure account with active subscription
- OpenAI API key
- Python 3.9+
- Azure Functions Core Tools
- Azure CLI

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/azure-article-generator.git
cd azure-article-generator
```

2. Create Azure resources:
- Function App (Python)
- Storage Account
- Create two containers in the storage account:
  - `raw-content`
  - `processed-content`

3. Configure local settings:
Create `local.settings.json`:
```json
{
    "IsEncrypted": false,
    "Values": {
        "AzureWebJobsStorage": "YOUR_STORAGE_CONNECTION_STRING",
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "COSMOS_CONNECTION_STRING": "YOUR_COSMOS_CONNECTION_STRING",
        "STORAGE_CONNECTION_STRING": "YOUR_STORAGE_CONNECTION_STRING",
        "OPENAI_API_KEY": "YOUR_OPENAI_KEY"
    }
}
```

4. Install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

## Local Development

1. Start the functions locally:
```bash
func start
```

2. Test the endpoints:
```bash
# Test input handler
curl -X POST http://localhost:7071/api/input -H "Content-Type: application/json" -d "{\"theme\":\"machine learning\"}"

# Test arXiv scraper
curl -X POST http://localhost:7071/api/arxiv -H "Content-Type: application/json" -d "{\"theme\":\"machine learning\", \"requestId\":\"test123\"}"

# Test Medium scraper
curl -X POST http://localhost:7071/api/medium -H "Content-Type: application/json" -d "{\"theme\":\"machine learning\", \"requestId\":\"test123\"}"

# Generate article
curl -X POST http://localhost:7071/api/generate -H "Content-Type: application/json" -d "{\"theme\":\"machine learning\", \"requestId\":\"test123\"}"
```

## Deployment

1. Deploy to Azure:
```bash
func azure functionapp publish your-function-app-name
```

2. Configure application settings in Azure Portal:
- Add all required connection strings and API keys
- Ensure both blob containers exist

## Using the Deployed API

Use Postman or any HTTP client with these endpoints:

1. Input Handler:
```
POST https://your-function-app.azurewebsites.net/api/input?code=YOUR_FUNCTION_KEY
Body: {"theme": "your theme"}
```

2. arXiv Scraper:
```
POST https://your-function-app.azurewebsites.net/api/arxiv?code=YOUR_FUNCTION_KEY
Body: {"theme": "your theme", "requestId": "your-request-id"}
```

3. Medium Scraper:
```
POST https://your-function-app.azurewebsites.net/api/medium?code=YOUR_FUNCTION_KEY
Body: {"theme": "your theme", "requestId": "your-request-id"}
```

4. Article Generator:
```
POST https://your-function-app.azurewebsites.net/api/generate?code=YOUR_FUNCTION_KEY
Body: {"theme": "your theme", "requestId": "your-request-id"}
```

The final article will be stored in the `processed-content` container in your Azure Storage account.

## Project Structure

```
azure-article-generator/
├── function_app.py     # Main application file with all functions
├── requirements.txt    # Python dependencies
├── host.json          # Host configuration
├── .gitignore
└── README.md
```

## Configuration

Required environment variables:
- `STORAGE_CONNECTION_STRING`: Azure Storage connection string
- `OPENAI_API_KEY`: Your OpenAI API key

## Error Handling

The system includes error handling for:
- Invalid input parameters
- API failures
- Storage access issues
- OpenAI API errors

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.