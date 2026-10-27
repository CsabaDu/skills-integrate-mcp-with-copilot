# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View an activity's faculty advisor and school contact
- Assign, update, or clear an advisor as an authenticated teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

4. Add teacher accounts to `src/teachers.json` before using staff-only endpoints:

   ```json
   {
     "teachers": {
       "teacher-username": {
         "password": "teacher-password"
       }
     }
   }
   ```

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| PUT    | `/activities/{activity_name}/advisor`                             | Assign/update with `{"advisor":{"name":"...","email":"..."}}` or clear with `{"advisor":null}`; requires teacher HTTP Basic credentials |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up
   - Optional faculty advisor name and school email

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
