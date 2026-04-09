# # COMP-3297-2026-group-D BetaTrax Sprint 2

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
1. Activate virtual environment: run `python -m venv venv` and then run `.\venv\Scripts\activate` and then run `pip install Django==6.0.2 djangorestframework django-filter`
reminder:
2. Run the server: `python manage.py runserver`
3. Admin panel: http://127.0.0.1:8000/admin/  
   (Username: `admin` / Password: `admin123abc`)
4. API endpoint: http://127.0.0.1:8000/api/defects/ -->this one for defects
5. http://127.0.0.1:8000/api/products/ -->this one for owner to add new products

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