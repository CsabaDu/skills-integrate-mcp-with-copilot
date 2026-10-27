# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Staff-only student registration and unregistration
- Teacher login with server-side authorization

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure a session signing key and teacher password hashes. Do not commit credentials or secrets to the repository. Generate a password hash with:

   ```
   python -c 'import getpass, hashlib, secrets; password=getpass.getpass("Teacher password: "); salt=secrets.token_hex(16); iterations=600000; print("pbkdf2_sha256$%d$%s$%s" % (iterations, salt, hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()))'
   ```

   Set `TEACHER_CREDENTIALS` to a JSON object mapping each teacher username to its generated hash, and set `SESSION_SECRET` to a long random value. For example:

   ```
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export TEACHER_CREDENTIALS='{"teacher1":"pbkdf2_sha256$600000$<salt>$<digest>"}'
   ```

   For local HTTP development only, set `SESSION_COOKIE_SECURE=false`. The secure cookie setting defaults to `true`; use HTTPS when teachers log in.

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                               |
| ------ | ----------------------------------------------------------------- | --------------------------------------------------------- |
| GET    | `/activities`                                                     | View activities and their current participants            |
| GET    | `/auth/status`                                                    | Check whether the current browser is signed in as a teacher |
| POST   | `/auth/login`                                                      | Sign in with a configured teacher username and password    |
| POST   | `/auth/logout`                                                     | Sign out                                                   |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | (Teacher only) Sign up a student                           |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | (Teacher only) Unregister a student                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and registration data remain in memory, so they are reset when the server restarts. Teacher sessions are stored in signed, HTTP-only cookies and expire after eight hours. In production, set `SESSION_SECRET` to the same secret across application workers and restarts, and serve the app over HTTPS.
