# Calendar Booking System

This project implements a simple calendar booking system, allowing Calendar Owners to set up their availability and enabling Invitees to book appointments through APIs.

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd calendar_booking_system
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Cache table
```bash
python manage.py createcachetable
```

### 6. Run the Application
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000`.

---

## API Documentation

### Swagger UI
For detailed API documentation and to try out endpoints, visit the Swagger UI:

```text
http://127.0.0.1:8000/swagger/
```

---

## Project Structure

- **calendar_system**: Contains project settings and configuration files.
- **core**: Core functionality of the system, including:
  - `models.py`: Database models.
  - `views.py`: API views for handling requests.
  - `serializers.py`: Data serializers for APIs.
  - `tests/`: Contains unit tests for core components.
  - `services/`: Business logic and helper functions.

---

## Assumptions

1. **User Management**: 
   - Calendar Owners are assumed to be pre-authenticated. No user registration or login functionality is implemented.

2. **Data Persistence**: 
   - The system uses SQLite for data storage. Persistence beyond runtime is implemented.

3. **Appointment Rules**: 
   - Appointments are of fixed 60-minute durations.
   - Time slots are generated based on the Calendar Owner's availability and existing appointments.
   - Double bookings are not allowed.

4. **Development Framework**: 
   - Django was used as the backend framework for modularity and speed.

5. **Additional Assumptions**:
   - Invitees must book using valid 60-minute slots retrieved from the `Search Available Time Slots` API.
   - No advanced validations (e.g., time zone support) are currently implemented.

---

## Features Implemented

1. **Availability Setup API**:
   - Allows Calendar Owners to define their availability.

2. **Search Available Time Slots API**:
   - Retrieves valid 60-minute slots for Invitees.

3. **Book Appointment API**:
   - Allows Invitees to book an available time slot.

4. **List Upcoming Appointments API**:
   - Displays upcoming appointments for Calendar Owners.

---

## Testing

### Running Tests
Run unit tests using `pytest`:
```bash
pytest
```

### Code Coverage with `coverage`
To check test coverage, use the `coverage` tool:

1. Install `coverage`:
   ```bash
   pip install coverage
   ```

2. Run tests with coverage tracking:
   ```bash
   coverage run --source='.' manage.py test
   ```

3. Generate a coverage report in the terminal:
   ```bash
   coverage report
   ```

4. Generate an HTML coverage report:
   ```bash
   coverage html
   ```

   The HTML report will be saved in the `htmlcov/` directory. Open `htmlcov/index.html` in your browser to view the detailed coverage report.

---

## Future Improvements

- Add authentication and authorization.
- Implement a frontend interface.
- Support for advanced time zones and recurring appointments.
- Integrate notification systems for booking confirmations.
