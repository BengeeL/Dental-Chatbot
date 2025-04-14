# Dental Chatbot - Frontend Client

This is the frontend application for the Dental Chatbot project, built with React, TypeScript, and Vite.

## Architecture Overview

The application consists of these main components:

- **Core Components:**

  - `Chatbot`: Interactive AI chat component that communicates with AWS Lex
  - `Home`: Main landing page with dental clinic information
  - `Footer`: Site-wide footer with clinic information

- **Key Features:**
  - Text-to-speech using AWS Polly
  - Speech-to-text using AWS Transcribe
  - Session-based conversation tracking
  - Responsive design for all device sizes

## Tech Stack

- React 19
- TypeScript
- Vite 6
- Axios for API calls
- CSS for styling (no additional frameworks)

## Environment Variables

The application uses different environment variables based on the build mode:

- `.env.development` - Used during development, points to localhost
- `.env.production` - Used for production builds, points to deployed AWS API

Required variables:

- `VITE_API_BASE_URL`: Points to the backend API endpoint

## Development Setup

1. Install dependencies:

   ```
   npm install
   ```

2. Start the development server:
   ```
   npm run dev
   ```

This will start the Vite development server, typically on http://localhost:5173.

## Building for Production

1. Create production build:

   ```
   npm run build
   ```

2. Preview the production build locally:
   ```
   npm run preview
   ```

The production build will use the `.env.production` configuration, connecting to your deployed AWS API Gateway endpoint.

## Deployment

After building, the contents of the `dist` folder can be deployed to any static website hosting service like:

- AWS S3 + CloudFront
- Netlify
- Vercel
- GitHub Pages

## Integration with Backend

The frontend communicates with the Chalice backend hosted on AWS Lambda through these key endpoints:

- `/chat`: Sends user messages to Amazon Lex and returns responses
- `/speech`: Converts text responses to speech using Amazon Polly
- `/transcribe`: Converts user voice recordings to text using Amazon Transcribe
- `/save-conversation`: Stores complete conversations to S3

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure
