# Dental Chatbot - Serverless Implementation

This directory contains the AWS Chalice serverless implementation of the Dental Chatbot backend.

## Project Structure

```
server_chalice/
├── app.py                  # Main Chalice application
├── chalicelib/             # Library code for the application
│   └── utils/              # Utility functions
│       ├── dynamo_utils.py # DynamoDB interaction utilities
│       ├── lex_utils.py    # Amazon Lex interaction utilities
│       ├── polly_utils.py  # Amazon Polly interaction utilities
│       ├── s3_utils.py     # S3 interaction utilities
│       └── transcribe_utils.py # Amazon Transcribe interaction utilities
├── .chalice/              # Chalice configuration
│   ├── config.json        # Chalice app configuration
│   └── iam-policy.json    # IAM policies for deployment
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Local Development

1. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the local development server:

   ```
   chalice local
   ```

   The API will be available at http://localhost:8000

   Note: The app uses environment variables from `.chalice/config.json` for configuration. There's no need for `.env` files.

## Environment Variables Configuration

All environment variables are configured in `.chalice/config.json`. This is the primary source of configuration for both local development and deployment.

Key environment variables:

- `LEX_BOT_ID`: ID of your Amazon Lex bot
- `LEX_BOT_ALIAS_ID`: Alias ID of your Lex bot
- `LEX_BOT_LOCALE_ID`: Locale ID (e.g., "en_US")
- `AWS_REGION`: AWS region to use (default: "ca-central-1")
- `DYNAMODB_TABLE`: DynamoDB table name for chat history
- `S3_BUCKET_NAME`: S3 bucket for storing conversations

## Deployment to AWS

1. Make sure you have AWS CLI installed and configured with appropriate credentials.

2. Deploy the application:

   ```
   chalice deploy
   ```

3. After deployment, Chalice will output the API Gateway URL. Update the client-side API endpoints to use this URL.
