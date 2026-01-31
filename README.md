# 🪐 Planetarium API

A RESTful API for managing planetarium operations, including movie shows, dome sessions, and ticket bookings. Built with **Django Rest Framework** and containerized with **Docker**.

## Key Features

* **JWT Authentication:** Secure user registration and login with Access/Refresh tokens.
* **Role-Based Access:** Standard users can book tickets; Admins can manage shows and sessions.
* **Atomic Transactions:** Ensures data integrity during ticket purchases (all-or-nothing bookings).
* **Smart Seat Validation:** Prevents double-booking and validates dome capacity in real-time.
* **Performance:** Optimized Database queries using `prefetch_related` and `select_related` to minimize N+1 problems.
* **Filtering:** Advanced filtering for Shows (by title, genre) and Sessions (by date).
* **Media Management:** Supports image uploads for movie posters.
* **Documentation:** Swagger & ReDoc UI.

## Tech Stack

* **Python 3.14** (Alpine)
* **Django 6 & DRF**
* **PostgreSQL**
* **Docker & Docker Compose**
* **drf-spectacular** (Swagger Docs)

---

## How to Run (Docker)

This is the recommended way to run the project.

### 1. Clone the repository
```bash
git clone https://github.com/toomuchtearz/api_planetarium.git
cd api_planetarium
```

### 2. Configure Environment
Create a `.env` file based on the example provided.

```bash
cp .env.example .env
```


### 3. Build and Run
Build the images and start the services. This command will automatically run migrations and start the server.

```bash
docker-compose up --build
```

### 4. Create a Superuser
To access the Admin features, create a superuser inside the running container:

```bash
docker-compose exec planetarium python manage.py createsuperuser
```

### 5. Steps to get the access token:

Go to -> http://127.0.0.1:8001/api/token/
1. Enter email, password and send a POST request
2. Copy the access token
3. Add it to headers with the 'Bearer' prefix 
4. Example: "Authorization: Bearer <token>"


### 6. Access the App

Once you have your JWT token, you can access API:

API Root: http://127.0.0.1:8001/api/planetarium/

Admin: http://127.0.0.1:8001/admin/

Swagger Docs: http://127.0.0.1:8001/api/doc/swagger/

---

## Tests
Run all tests in Docker:

```bash
docker-compose exec planetarium python manage.py test
```

---

## API Documentation
The API is fully documented using Swagger/OpenAPI.

**Endpoints Overview:**
![API Screenshot](<img width="1512" height="1078" alt="image" src="https://github.com/user-attachments/assets/8335aaab-9f1c-4446-9356-76d6a6790787" />)

1. Run the project. 
2. Go to `/api/doc/swagger/`.

Authentication:

1. Click the **Authorize** button.
2. Register a user or get a token via `/api/user/token/`.
3. Enter your token (e.g., `<your_token>`).

---

## Project Structure
```text
planetarium-api/
├── planetarium/      # Main app (Models, Views, Serializers)
├── user/             # User management & Auth
├── api_planetarium/  # Project settings
├── media/            # Uploaded images (Volume mapped)
├── Dockerfile
├── docker-compose.yml
└── manage.py
```
