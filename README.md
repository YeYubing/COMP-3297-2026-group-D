# # COMP-3297-2026-group-D BetaTrax Sprint 2

## Project Overview
BetaTrax is a defect tracking system developed using **Django 6.0.2** and **Django Rest Framework (DRF)**.


## Sprint 2 Enhancements over Sprint 1
- ✅ Product Owner can assign multiple developers when registering a product – Only developers who are not already assigned to another product are available for selection. A developer cannot be responsible for more than one product at a time.
- ✅ Restricted status transitions for Product Owner and Developer – State changes follow strict business rules:
  -Product Owner can only change: new → open, rejected, duplicate; fixed → reopened, resolved.
  -Developer can only change: open / reopened → assigned; assigned → fixed, cannot_reproduce.
- ✅ Duplicate defect handling with email merging – When a Product Owner marks a defect as duplicate, they must provide a target_defect_id. The current defect’s tester email(s) are merged into the target defect’s tester email list. As a result, when the target defect’s status changes, all testers (including those from the duplicate) receive notifications.
- ✅ Full comment system for Product Owners and Developers – Both roles can add comments to any defect they have access to. Each comment includes author, timestamp, and text, and is automatically assigned a unique comment ID.
- ✅ Automatic email notifications on every status change – Whenever a defect’s status changes, an email is sent to all email addresses listed in the defect’s tester_email field (supports multiple comma‑separated emails).
- ✅ Auto‑generated User ID for each new user – When an administrator creates a user account, a unique user ID is automatically generated and stored (in addition to the default id field).
- ✅ Filtering functionality – Product Owners and Developers can filter defect reports related to their own products using custom filters (e.g., by status, severity, priority, or date).
- ✅ Role‑based restrictions on actions:
  -Testers can submit defect reports but cannot register products.
  -Developers can modify defects but cannot register products.
  -Product Owners can register products but cannot submit defect reports.

## How to Run
1. Activate virtual environment: run `python -m venv venv` and then run `.\venv\Scripts\activate` and then run `pip install Django==6.0.2 djangorestframework django-filter`
2. Run the server: `python manage.py runserver`
3. Root URL: http://127.0.0.1:8000/ now redirects to the API landing page at http://127.0.0.1:8000/api/  
4. Admin panel: http://127.0.0.1:8000/admin/  
5. API endpoint: http://127.0.0.1:8000/api/defects/ -->this one for developers and owners to review the reports
                 http://127.0.0.1:8000/api/products/ -->this one for owners to add new products
6. View defect reports: Open http://127.0.0.1:8000/api/defects/<id>/ (e.g., http://127.0.0.1:8000/api/defects/1/) in your browser after logging in.
7. View products: Open http://127.0.0.1:8000/api/products/<id>/ (e.g., http://127.0.0.1:8000/api/products/1/) in your browser after logging in.
## Limitations (Sprint 2)
- The function of sending emails has not been debugged yet. It's impossible to really send emails in real life
- Comment system does not support editing or deleting comments
-The field named product_id in the source code actually represents the product name in practice. Separately, when a product is registered, a unique system-generated ID is automatically created. This system ID is used to open the corresponding product interface.

--
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

