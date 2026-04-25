# # COMP-3297-2026-group-D BetaTrax Sprint 1

## Project Overview
BetaTrax is a defect tracking system developed using **Django 6.0.2** and **Django Rest Framework (DRF)**.

This Sprint 1 delivers the core end-to-end defect lifecycle:
- New → Open → Assigned → Fixed → Resolved
- Email notifications are sent on status changes (printed to console for Sprint 1).

## Implemented Features
- ✅ Tester can submit a defect report with email address
- ✅ Product Owner can view, evaluate, accept defect and set Severity & Priority
- ✅ Developer can view and take responsibility for a defect (Assigned) and mark it as Fixed
- ✅ Product Owner can close the defect as Resolved
- ✅ Automatic email notifications on every status change
- ✅ Full Django Admin interface for easy management
- ✅ RESTful API for all operations (`/api/defects/`)

## How to Run
1. Activate virtual environment: run `python -m venv venv` and then run `.\venv\Scripts\activate` and then run `pip install Django==6.0.2 djangorestframework`
2. Run the server: `python manage.py runserver`
3. Admin panel: http://127.0.0.1:8000/admin/  
   (Username: `admin` / Password: `admin123abc`)
4. API endpoint: http://127.0.0.1:8000/api/defects/   ， http://127.0.0.1:8000/api/products/

## Limitations (Sprint 1)
- Only supports **one registered product** (registered via Django Admin)
- User registration is done via Django Admin (no custom registration page)
- Emails are printed to console only (using `console.EmailBackend`)
- No frontend UI (API only, as required for Sprint 1)

## Requirements
See `requirements.txt` for all installed packages.

## Team Contributions
- *: Defect Model, DRF API, serializers, views, email notifications, Admin configuration


## Submission Notes
- This is the complete Sprint 1 source code as required.
- All required slices from the Task Sheet have been implemented.

---

## How to Run PostgreSQL Multi-Tenants (Local Development)

1. **Set up the database**
   - Make sure PostgreSQL is running. Then create the database and user (example using psql):

     ```sql
     CREATE USER betatrax_user WITH PASSWORD 'your_password';
     CREATE DATABASE betatrax_db OWNER betatrax_user;
     ALTER USER betatrax_user CREATEDB;
     ```

     *Note: Update line 67 in settings.py with the PASSWORD set to 'your_password'*

2. **Clone / unzip the project and create a virtual environment**

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   *(requirements.txt includes Django, DRF, django-tenants, psycopg2-binary, coverage, etc.)*

4. **Configure database (if needed)**
   - Open `BetaTrax/settings.py` and verify the DATABASES section matches your PostgreSQL credentials.
   - The engine must be `django_tenants.postgresql_backend`.

5. **Apply migrations**

   ```bash
   python manage.py makemigrations tenants defects
   python manage.py migrate_schemas
   ```

6. **Create a superuser (shared across all tenants)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Create your first tenant and domain**

   ```bash
   python manage.py shell
   ```

   Inside the shell:

   ```python
   from tenants.models import Client, Domain

   tenant = Client(schema_name='dev', name='Dev Company')
   tenant.save()

   domain = Domain()
   domain.domain = 'dev.localhost'
   domain.tenant = tenant
   domain.is_primary = True
   domain.save()
   exit()
   ```

8. **Update your local hosts file**
   - Add the following line to the last row of your hosts file:
     - Windows: `C:\Windows\System32\drivers\etc\hosts`
     - macOS/Linux: `/etc/hosts`

     ```
     127.0.0.1  dev.localhost
     ```

9. **Run the server**

   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Admin panel: http://dev.localhost:8000/admin/ (use the superuser you created)
    - API endpoints:
      - http://dev.localhost:8000/api/defects/
      - http://dev.localhost:8000/api/products/

To add more tenants (e.g., test1.localhost), repeat steps 7–8 with a different schema_name and domain.

