# Frontend API Integration Guide - Production RAG

This document outlines the complete API flow, required endpoints, authentication methods, and where each API should be integrated into the frontend application.

## Base Configuration

**Base URL:** `http://localhost:8000/api/v1` (or your production API URL)
**Authentication:** Most endpoints require a Bearer token.
- Header format: `Authorization: Bearer <your_access_token>`

> [!IMPORTANT]
> The `/auth/login` endpoint returns a standard OAuth2 token response. You must store the `access_token` securely (e.g., in an HttpOnly cookie or secure local storage) and attach it to all subsequent requests.

---

## 1. Authentication Flow

**Where to integrate:** Login page, Registration page, Global app state (AuthProvider).

### Register User
- **Endpoint:** `POST /auth/register`
- **Payload:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }
  ```
- **Response:** User details (id, email, full_name)

### Login User
- **Endpoint:** `POST /auth/login`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Payload:** `username=user@example.com&password=securepassword`
- **Response:** 
  ```json
  {
    "access_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

---

## 2. RAG Query & Chat Flow

**Where to integrate:** Main Chatbot UI, Search Bar.

### Submit Query
- **Endpoint:** `POST /query`
- **Requires Auth:** Yes
- **Payload:**
  ```json
  {
    "query": "What are the company policies regarding remote work?",
    "filters": {} // Optional metadata filters
  }
  ```
- **Response:**
  ```json
  {
    "answer": "Remote work is permitted up to 3 days a week...",
    "source_documents": [
      {"content": "...", "metadata": {"source": "policy.pdf"}}
    ],
    "tokens_used": 145
  }
  ```

---

## 3. Usage History Flow

**Where to integrate:** Chat sidebar (Recent Queries), User Profile/Dashboard.

### List History
- **Endpoint:** `GET /history`
- **Requires Auth:** Yes
- **Response:**
  ```json
  {
    "logs": [
      {
        "id": "60d5ec...",
        "query_text": "What is our leave policy?",
        "answer_text": "...",
        "created_at": "2026-05-13T10:00:00Z"
      }
    ],
    "total_queries": 10,
    "total_tokens": 1500
  }
  ```

### Delete History Item
- **Endpoint:** `DELETE /history/{log_id}`
- **Requires Auth:** Yes

---

## 4. Document Management Flow

**Where to integrate:** Document Upload Portal, File Manager Dashboard.

### Upload Document
- **Endpoint:** `POST /documents/upload`
- **Content-Type:** `multipart/form-data`
- **Payload:** Form data with `file` field.
- **Requires Auth:** Yes
- **Response:** Returns document metadata and ID.

### Ingest Document (Process for RAG)
- **Endpoint:** `POST /documents/ingest`
- **Requires Auth:** Yes
- **Payload:**
  ```json
  {
    "document_ids": ["doc_id_1", "doc_id_2"]
  }
  ```
- **Response:** Returns a `job_id`.

### Check Ingestion Job Status
- **Endpoint:** `GET /documents/jobs/{job_id}`
- **Requires Auth:** Yes
- **Response:**
  ```json
  {
    "job_id": "uuid-...",
    "status": "completed" // queued, processing, completed, failed
  }
  ```
*Note: The frontend should poll this endpoint or use websockets (if implemented) to show processing progress.*

### List Documents
- **Endpoint:** `GET /documents`
- **Requires Auth:** Yes

### View/Download Document
- **Endpoint:** `GET /documents/{doc_id}/content`
- **Requires Auth:** Yes
- **Response:** Streams the binary file content.

### Delete Document
- **Endpoint:** `DELETE /documents/{doc_id}`
- **Requires Auth:** Yes

---

## 5. Admin Dashboard Flow (CRUD)

**Where to integrate:** Admin Settings, Resource Management Pages (Tenants, Users, Roles, etc.).

All admin routes follow standard RESTful patterns and require Auth. The endpoints are:
- `/admin/tenants`
- `/admin/departments`
- `/admin/tags`
- `/admin/roles`
- `/admin/sessions`
- `/admin/users`

### Standard Operations for each resource (e.g., Tenants):
- **List:** `GET /admin/tenants?skip=0&limit=50`
- **Get One:** `GET /admin/tenants/{tenant_id}`
- **Create:** `POST /admin/tenants`
- **Update:** `PATCH /admin/tenants/{tenant_id}`
- **Delete:** `DELETE /admin/tenants/{tenant_id}`

---

## 6. Evaluations Flow

**Where to integrate:** QA/Testing Dashboard, Admin Evaluation Page.

### Evaluate RAG Sample
- **Endpoint:** `POST /evaluations/rag`
- **Requires Auth:** Optional/Depending on config
- **Payload:**
  ```json
  {
    "query": "...",
    "answer": "...",
    "contexts": ["..."]
  }
  ```

## Summary of Integration Lifecycle
1. **App Init:** Check for `access_token` in local storage. If absent, redirect to `/login`.
2. **Dashboard Load:** Fetch `/history` to populate sidebar and `/documents` to populate the file manager.
3. **Chat Interaction:** User types message -> `POST /query` -> Display response and update token usage stats.
4. **Document Upload:** User drops file -> `POST /documents/upload` -> On success, automatically trigger `POST /documents/ingest` -> Poll `GET /documents/jobs/{job_id}` until complete.
5. **Admin Navigation:** Fetch respective `/admin/*` routes when navigating to settings panels.
