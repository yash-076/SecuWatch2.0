# 🚀 SecuWatch 2.0: Cloud Deployment Guide

This guide explains how to deploy the SecuWatch 2.0 Backend on **Render** (using Docker) and the Frontend on **Vercel** (Vite SPA).

---

## 1. Prepare Your Repository
Push your complete `SecuWatch2.0` repository (containing the `Backend`, `Frontend`, and `agent` directories) to a private GitHub, GitLab, or Bitbucket repository.

---

## 2. Deploying the Backend on Render

Render will host the FastAPI app as a containerized web service.

### Step 1: Set Up Databases on Render
1.  **PostgreSQL**:
    *   In Render Dashboard, click **New** -> **PostgreSQL**.
    *   Provide a name (e.g. `secuwatch-db`), database name, and region.
    *   Click **Create Database**.
    *   Once created, copy the **Internal Database URL** (if deploying backend on Render) or **External Database URL** (for remote queries).
2.  **Redis**:
    *   Click **New** -> **Redis**.
    *   Provide a name (e.g. `secuwatch-cache`) and region.
    *   Click **Create Redis**.
    *   Copy the **Internal Redis Connection String** (e.g. `redis://red-xxxxxxxx:6379`).

### Step 2: Deploy the FastAPI Web Service
1.  In Render Dashboard, click **New** -> **Web Service**.
2.  Connect your GitHub repository.
3.  Configure the service details:
    *   **Name**: `secuwatch-backend`
    *   **Root Directory**: `Backend` (Render will build inside this sub-folder)
    *   **Runtime**: `Docker` (Render auto-detects `Backend/Dockerfile`)
4.  Click **Advanced** to add environment variables:
    *   `DATABASE_URL`: (Paste your Render PostgreSQL connection string)
    *   `REDIS_URL`: (Paste your Render Redis connection string)
    *   `SECRET_KEY`: (A random secure string e.g. `openssl rand -hex 32`)
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: `30`
    *   `REFRESH_TOKEN_EXPIRE_DAYS`: `7`
    *   `AUTO_CREATE_DATABASE`: `true`
    *   `APP_LOG_LEVEL`: `info`
    *   `GEMINI_API_KEY`: (Optional — your Gemini AI key)
    *   `LLM_MODEL`: (e.g. `gemini-1.5-flash`)
5.  Click **Create Web Service**.
6.  Render will pull the code, build the Docker image, and deploy. Once finished, copy the public URL (e.g. `https://secuwatch-backend.onrender.com`).

---

## 3. Deploying the Frontend on Vercel

Vercel will compile the Vite + React app and host it as a fast, globally-distributed Static Single Page Application.

### Step 1: Set Up Project on Vercel
1.  Log in to the [Vercel Dashboard](https://vercel.com).
2.  Click **Add New** -> **Project**.
3.  Import the same GitHub repository.
4.  Configure the project settings:
    *   **Project Name**: `secuwatch-dashboard`
    *   **Framework Preset**: `Vite` (Vercel should auto-detect this)
    *   **Root Directory**: `Frontend`
5.  Open **Environment Variables** and add the following:
    *   **Key**: `VITE_API_BASE_URL`
    *   **Value**: (Your deployed Render backend URL e.g. `https://secuwatch-backend.onrender.com`)
    *   *Warning: Do not append a trailing slash to the backend URL.*
6.  Click **Deploy**.
7.  Vercel will install dependencies, execute `npm run build`, copy the output static assets via the SPA rewrite rules in `vercel.json`, and expose the public URL (e.g., `https://secuwatch-dashboard.vercel.app`).

---

## 4. Connecting Remote Agents

Now that your SecuWatch platform is live in the cloud:

1.  Open the deployed Vercel frontend in your browser.
2.  Sign up an organization user.
3.  Go to the **Devices** page and add a new target device. Copy the API Key.
4.  On the remote target machine, configure `agent/.env` to point to the live Render backend:
    ```env
    SECUWATCH_BACKEND_URL=https://secuwatch-backend.onrender.com
    SECUWATCH_DEVICE_ID=your_device_numerical_id
    SECUWATCH_API_KEY=your_copied_device_api_key
    ```
    The agent will stream alerts across the internet securely to your Render server, and you'll see them immediately on your Vercel client!

---

## 5. Integrating Apache Kafka in Production (Optional)

SecuWatch runs a **hybrid log processing model**. You can deploy it with or without a Kafka broker:

### A. Minimal Setup: No Kafka (Default Fallback)
If you do not configure any Kafka variables, the backend automatically detects that Kafka is down and falls back to **immediate processing**. Logs will be parsed, database alerts saved, and WebSocket updates dispatched instantly inside the API thread. This is perfect for initial setups and smaller scale deployments.

### B. Scalable Setup: With Apache Kafka
For high-volume logging environments, you can leverage Kafka to decouple ingestion from threat parsing:

1.  **Provision a Managed Kafka Cluster**:
    *   Create a Kafka cluster on a service like [Upstash Kafka](https://upstash.com/) or [Confluent Cloud](https://confluent.cloud/).
    *   Retrieve the **Bootstrap Server URL** (e.g. `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`) and access credentials.
2.  **Add Kafka Variables to Render Web Service**:
    Under Render Web Service -> **Environment**, add:
    *   `KAFKA_BOOTSTRAP_SERVERS`: `your-kafka-host:port`
    *   `KAFKA_REPLICATION_FACTOR`: `1` (or matching your cluster partition sizing)
3.  **Deploy Background Workers for Consumers on Render**:
    Since consumers run infinite poll loops, they must run as separate background processes.
    *   On Render, click **New** -> **Background Worker**.
    *   Connect your GitHub repository.
    *   **Root Directory**: `Backend`
    *   **Runtime**: `Docker`
    *   Add the same environment variables (`DATABASE_URL`, `REDIS_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `SECRET_KEY`).
    *   **Start Command**: Customize the Docker Entrypoint CMD for the consumers. Set the Start Command on Render overrides to run the respective consumer scripts:
        *   **Log Event Parser Worker**:
            *   Command: `python consumers/log_consumer.py`
        *   **Alert Broadcast Worker**:
            *   Command: `python consumers/alert_consumer.py`
        *   **Heartbeat Monitor Worker**:
            *   Command: `python consumers/heartbeat_consumer.py`
4.  Once deployed, Render Web Service will ingest logs and put them in Kafka. The Background Workers will consume the logs, evaluate alert threat signatures asynchronously, commit to Postgres, and stream the finalized alerts back to your browser.

