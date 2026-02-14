# Secure Authentication & Authorization Service

A production-ready RESTful backend built with **FastAPI**, **PostgreSQL**, and **Redis**. This service implements the complete OAuth 2.0 flow, JWT session management, and Role-Based Access Control (RBAC).

## Overview

This service provides a robust foundation for modern web applications, focusing on security best practices and scalability.

### Core Features
- **Local Authentication**: Secure registration and login using `bcrypt` password hashing.
- **Social Login (OAuth 2.0)**: Integration with **Google** and **GitHub** for a seamless user experience.
- **JWT Session Management**: Stateless authentication with short-lived **Access Tokens** (15 min) and long-lived **Refresh Tokens** (7 days).
- **RBAC (Role-Based Access Control)**: Middleware-enforced permissions for `User` and `Admin` roles.
- **Rate Limiting**: Redis-backed protection on sensitive endpoints (`/login`, `/register`) to mitigate brute-force attacks.
- **Containerization**: Fully orchestrated environment using Docker and Docker Compose.

---

## Architecture



The system is composed of three main services:
1. **API (FastAPI)**: Handles business logic, JWT generation, and OAuth callbacks.
2. **Database (PostgreSQL)**: Stores user profiles and linked OAuth provider accounts.
3. **Cache (Redis)**: Manages rate-limiting counters and session state.

---

## Setup and Installation

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Git](https://git-scm.com/) installed.

### One-Command Startup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd auth-service
   ```

2. **Initialize Environment Variables**

    ```bash
    cp .env.example .env
    ```

> The default values in `.env.example` are pre-configured for immediate local testing.

---

3. **Launch the Containerized Environment**

    ```bash
    docker-compose up --build
    ```

The API will be live at:
`http://localhost:8000`

The database will automatically seed with test credentials upon startup.

---

## Testing

### Automated Tests

This project uses **pytest** for integration testing.

To run the test suite within the Docker environment:

```bash
docker-compose exec app pytest
```

## Manual Testing (Seeded Credentials)

Use the following credentials to test the API via **curl** or **Postman**:

| Role          | Email              | Password              |
|--------------|--------------------|------------------------|
| Admin        | admin@example.com  | AdminPassword123!     |
| Regular User | user@example.com   | UserPassword123!      |


## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|------------|---------------|
| GET | `/health` | Service health status | No |
| POST | `/api/auth/register` | Create a new account | No |
| POST | `/api/auth/login` | Email/Password login | No |
| POST | `/api/auth/refresh` | Rotate access token | No |
| GET | `/api/auth/google` | Google login initiation | No |
| GET | `/api/auth/github` | GitHub login initiation | No |
| GET | `/api/users/me` | Retrieve current user profile | Yes |
| PATCH | `/api/users/me` | Update personal details | Yes |
| GET | `/api/users` | List all users (Admin only) | Admin Only |

## Security Best Practices Implemented

- **No Hardcoded Secrets**  
  All configuration values are loaded via environment variables.

- **Secure Password Storage**  
  Passwords are never stored in plain text.  
  `passlib` with **bcrypt** is used for secure hashing.

- **Database Safety**  
  Uses **SQLAlchemy ORM** to prevent SQL injection attacks.

- **Rate Limiting**  
  Limits login attempts to **10 requests per minute per IP** to mitigate credential stuffing attacks.
