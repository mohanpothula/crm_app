**CRM Contacts API**
A simple CRM backend built using FastAPI and SQLite.

** How to Run**

**1. Install dependencies**
pip install fastapi uvicorn pydantic email-validator

**2. Start the API server**
From the project root:

uvicorn crm_api.main:app --reload --host 0.0.0.0 --port 8000

This automatically creates contacts.db if it does not exist.

**3. Open API documentation**

Visit:

http://localhost or public ip:8000/docs


**Implemented Endpoints**

POST /contacts

Create a new contact.
**Validations:
Missing name → 422**


**Invalid email → 422


Duplicate email → 409**



**GET /contacts**

List contacts.
Query params supported:
company=Acme


limit=5


offset=10


sort_by=id|name|company


order=asc|desc



**GET /contacts/{id}**
Retrieve a single contact by ID.
404 if not found



DELETE /contacts/{id}
Delete a contact.
204 on success


404 if not found



**Example Requests**

Create contact
curl -X POST http://localhost:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@test.com"}'

**List contacts**
curl "http://localhost:8000/contacts?limit=5&offset=0&sort_by=name&order=asc"

**Filter by company**
curl "http://localhost:8000/contacts?company=Acme"

Get contact
curl "http://localhost:8000/contacts/1"

Delete contact
curl -X DELETE "http://localhost:8000/contacts/1"


