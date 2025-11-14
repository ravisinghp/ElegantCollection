# Microsoft Login & Email Attachment Extractor (FastAPI Backend)

This project is a FastAPI backend that enables users to log in with their Microsoft account, fetches their emails via Microsoft Graph API, and downloads attachments from emails containing specific keywords.

## Features

- **Microsoft OAuth2 Login:** Secure authentication using Microsoft accounts.
- **Fetch Emails:** Retrieve emails from the user's Outlook inbox.
- **Download Attachments:** Automatically download attachments from emails containing keywords like "search", "research", or "r&d".
- **REST API Endpoints:** Easy integration with any frontend.

## Folder Structure

```
backend/
├── app/
│   ├── main.py
│   ├── routers/
│   │   └── auth.py
│   └── services/
│       └── auth_service.py
├── attachments/
├── .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
```

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd backend
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the following content:

```
CLIENT_ID=your-microsoft-client-id
CLIENT_SECRET=your-microsoft-client-secret
TENANT_ID=your-microsoft-tenant-id
REDIRECT_URI=http://localhost:8000/auth/callback
GRAPH_API_ENDPOINT=https://graph.microsoft.com/v1.0
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Run the Application

```sh
uvicorn app.main:app --reload
```

Or use Docker:

```sh
docker-compose up
```

## API Endpoints

- **GET `/auth/login`**  
  Returns the Microsoft OAuth2 login URL.

- **GET `/auth/callback`**  
  Handles the OAuth2 callback and exchanges the code for an access token.

- **POST `/auth/emails`**  
  Fetches emails and downloads attachments.  
  **Body:** `{ "access_token": "<token>" }`

## How It Works

1. **User logs in** via Microsoft OAuth2.
2. **Backend exchanges code** for an access token.
3. **Frontend sends token** to `/auth/emails`.
4. **Backend fetches emails** and downloads relevant attachments to the `attachments/` folder.

## License

This project is licensed under the MIT License.
