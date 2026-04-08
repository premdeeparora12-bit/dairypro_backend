# DairyPro Management System: Go-Live Guide

This guide provides simple steps to deploy your DairyPro Management System, which consists of a FastAPI backend and a static HTML/JavaScript frontend.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your server:

*   **Python 3.8+**: The backend is built with FastAPI, which requires Python.
*   **pip**: Python's package installer.
*   **Git**: For cloning the project repository (optional, but recommended).
*   **A web server (e.g., Nginx, Apache)**: To serve the static files and proxy requests to the FastAPI backend.
*   **A process manager (e.g., Gunicorn, PM2)**: To run the FastAPI application in production.

## 2. Project Setup

1.  **Clone the repository (if applicable) or transfer files**: 
    If you are using Git, clone your project to your server:
    ```bash
    git clone <your-repository-url>
    cd dairypro
    ```
    Otherwise, transfer the `dairypro` directory containing `main.py`, `requirements.txt`, and the `templates` and `static` folders to your server.

2.  **Install Python dependencies**: 
    Navigate to the `dairypro` directory and install the required Python packages:
    ```bash
    cd /path/to/your/dairypro
    pip install -r requirements.txt
    ```

## 3. Running the FastAPI Backend

For production, it's recommended to use a production-ready ASGI server like Gunicorn with Uvicorn workers.

1.  **Install Gunicorn**: 
    ```bash
    pip install gunicorn
    ```

2.  **Start the FastAPI application with Gunicorn**: 
    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
    ```
    *   `-w 4`: Runs 4 worker processes (adjust based on your server's CPU cores).
    *   `-k uvicorn.workers.UvicornWorker`: Specifies Uvicorn workers for FastAPI.
    *   `main:app`: Refers to the `app` object within `main.py`.
    *   `--bind 0.0.0.0:8000`: Binds the application to all network interfaces on port 8000.

    You can run this command in a `screen` or `tmux` session to keep it running after you close your terminal, or configure it as a systemd service for automatic startup.

## 4. Serving the Frontend with Nginx (Example)

This example uses Nginx to serve the static `index.html` and proxy API requests to your FastAPI backend.

1.  **Install Nginx**: 
    ```bash
    sudo apt update
    sudo apt install nginx
    ```

2.  **Create an Nginx configuration file**: 
    Create a new file, e.g., `/etc/nginx/sites-available/dairypro`, with the following content:
    ```nginx
    server {
        listen 80;
        server_name your_domain.com www.your_domain.com; # Replace with your domain

        root /path/to/your/dairypro/templates; # Path to your index.html
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }

        location /api {
            proxy_pass http://127.0.0.1:8000; # Address where Gunicorn is running
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Optional: Serve static assets from the 'static' directory
        location /static {
            alias /path/to/your/dairypro/static/; # Path to your static files
        }
    }
    ```
    **Important**: Replace `your_domain.com` and `/path/to/your/dairypro` with your actual domain and project path.

3.  **Enable the Nginx configuration**: 
    ```bash
    sudo ln -s /etc/nginx/sites-available/dairypro /etc/nginx/sites-enabled/
    sudo nginx -t # Test Nginx configuration for syntax errors
    sudo systemctl restart nginx
    ```

## 5. Database Management

The application uses an SQLite database (`dairypro.db`) by default. This file will be created in the same directory as `main.py` when the application runs for the first time. For more robust deployments, consider using a PostgreSQL or MySQL database.

## 6. Going Live

After completing the above steps, your DairyPro Management System should be accessible via your configured domain. Ensure your domain's DNS records point to your server's IP address.

**Author**: Manus AI
