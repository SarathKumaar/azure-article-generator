import azure.functions as func
import logging
import json
import os
from azure.storage.blob import BlobServiceClient
import arxiv
import requests
from bs4 import BeautifulSoup
import openai
from datetime import datetime

app = func.FunctionApp()

@app.route(route="input", auth_level=func.AuthLevel.FUNCTION)
def input_handler(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Input handler triggered.')
    
    try:
        req_body = req.get_json()
        theme = req_body.get('theme')
        
        if not theme:
            return func.HttpResponse(
                "Please provide a theme in the request body",
                status_code=400
            )
            
        return func.HttpResponse(
            json.dumps({"theme": theme, "status": "accepted"}),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )

@app.route(route="arxiv", auth_level=func.AuthLevel.FUNCTION)
def arxiv_scraper(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('arXiv scraper triggered.')
    
    try:
        # Get request data
        req_body = req.get_json()
        theme = req_body.get('theme')
        request_id = req_body.get('requestId')
        
        # Configure arXiv client
        search = arxiv.Search(
            query = theme,
            max_results = 5,
            sort_by = arxiv.SortCriterion.Relevance
        )
        
        # Get results
        results = []
        for paper in search.results():
            results.append({
                'title': paper.title,
                'summary': paper.summary,
                'authors': [author.name for author in paper.authors],
                'url': paper.pdf_url,
                'published': paper.published.isoformat(),
                'updated': paper.updated.isoformat()
            })
        
        # Store in blob storage
        connection_string = os.environ["STORAGE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client("raw-content")
        
        blob_name = f"arxiv_{request_id}.json"
        container_client.upload_blob(
            name=blob_name,
            data=json.dumps(results, indent=2),
            overwrite=True
        )
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "papers_found": len(results),
                "blob_name": blob_name
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in arXiv scraper: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )

@app.route(route="medium", auth_level=func.AuthLevel.FUNCTION)
def medium_scraper(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Medium scraper triggered.')
    
    try:
        # Get request data
        req_body = req.get_json()
        theme = req_body.get('theme')
        request_id = req_body.get('requestId')
        
        # Search Medium (simplified version)
        search_url = f"https://medium.com/search?q={theme}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract articles (simplified)
        results = []
        articles = soup.find_all('article')[:5]  # Limit to 5 articles
        
        for article in articles:
            results.append({
                'title': article.get_text()[:100],
                'url': article.find('a').get('href') if article.find('a') else None
            })
        
        # Store in blob storage
        connection_string = os.environ["STORAGE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client("raw-content")
        
        blob_name = f"medium_{request_id}.json"
        container_client.upload_blob(
            name=blob_name,
            data=json.dumps(results, indent=2),
            overwrite=True
        )
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "articles_found": len(results),
                "blob_name": blob_name
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in Medium scraper: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )

@app.route(route="generate", auth_level=func.AuthLevel.FUNCTION)
def article_generator(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Article generator triggered.')
    
    try:
        # Get request data
        req_body = req.get_json()
        theme = req_body.get('theme')
        request_id = req_body.get('requestId')
        
        # Get blob content
        connection_string = os.environ["STORAGE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client("raw-content")
        
        # Read content from both sources
        arxiv_blob = container_client.get_blob_client(f"arxiv_{request_id}.json")
        medium_blob = container_client.get_blob_client(f"medium_{request_id}.json")
        
        arxiv_content = json.loads(arxiv_blob.download_blob().readall())
        medium_content = json.loads(medium_blob.download_blob().readall())
        
        # Prepare prompt
        prompt = f"""Create a comprehensive Medium-style article about {theme}.
        
        Use these research papers as primary sources:
        {json.dumps(arxiv_content, indent=2)}
        
        And reference these Medium articles:
        {json.dumps(medium_content, indent=2)}
        
        The article should:
        1. Have a clear introduction
        2. Include technical details from research papers
        3. Reference practical applications
        4. Include examples and explanations
        5. End with conclusions and future implications
        
        Format the article in Markdown."""
        
        # Generate article using OpenAI (new syntax)
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional technology writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        article = response.choices[0].message.content
        
        # Store generated article
        output_container_client = blob_service_client.get_container_client("processed-content")
        output_blob_name = f"article_{request_id}.md"
        output_container_client.upload_blob(
            name=output_blob_name,
            data=article,
            overwrite=True
        )
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "article_blob": output_blob_name,
                "requestId": request_id
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in article generator: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )