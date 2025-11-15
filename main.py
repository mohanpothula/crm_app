from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime
import sqlite3

app = FastAPI(title="CRM Contacts API")

DB_PATH = "contacts.db"


# ---------------------------------------
# Database initialization
# ---------------------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            company TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

init_db()


# ---------------------------------------
# Pydantic Models
# ---------------------------------------
class ContactBase(BaseModel):
    name: constr(min_length=1, strip_whitespace=True)
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class Contact(ContactBase):
    id: int
    created_at: datetime


class ContactListResponse(BaseModel):
    data: List[Contact]
    count: int
    limit: int
    offset: int


# ---------------------------------------
# Helper function
# ---------------------------------------
def row_to_contact(row):
    return Contact(
        id=row[0],
        name=row[1],
        email=row[2],
        phone=row[3],
        company=row[4],
        created_at=row[5]
    )


# ---------------------------------------
# GET /contacts
# ---------------------------------------
@app.get("/contacts", response_model=ContactListResponse)
def get_contacts(
    company: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("id", pattern="^(name|company|id)$"),
    order: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    query = "SELECT * FROM contacts WHERE 1=1"
    params = []

    if company:
        query += " AND LOWER(company) = LOWER(?)"
        params.append(company)

    if search:
        query += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])

    # Count matching
    count_query = f"SELECT COUNT(*) FROM ({query})"
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute(count_query, params).fetchone()[0]

    # Sorting + pagination
    query += f" ORDER BY {sort_by} {order.upper()} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(query, params).fetchall()
        contacts = [row_to_contact(r) for r in rows]

    return ContactListResponse(
        data=contacts,
        count=total,
        limit=limit,
        offset=offset
    )


# ---------------------------------------
# GET /contacts/{id}
# ---------------------------------------
@app.get("/contacts/{id}", response_model=Contact)
def get_contact(id: int = Path(..., gt=0)):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")

    return row_to_contact(row)


# ---------------------------------------
# POST /contacts
# ---------------------------------------
@app.post("/contacts", response_model=Contact, status_code=201)
def create_contact(contact: ContactCreate):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO contacts (name, email, phone, company) VALUES (?, ?, ?, ?)",
                (contact.name, contact.email, contact.phone, contact.company)
            )
            conn.commit()
            new_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Email already exists")

        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (new_id,)).fetchone()
        return row_to_contact(row)


# ---------------------------------------
# PUT /contacts/{id}
# ---------------------------------------
@app.put("/contacts/{id}", response_model=Contact)
def update_contact(contact: ContactUpdate, id: int = Path(..., gt=0)):

    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Contact not found")

        # Check duplicate email if changed
        if contact.email != existing[2]:
            dup = conn.execute(
                "SELECT 1 FROM contacts WHERE email = ?", (contact.email,)
            ).fetchone()
            if dup:
                raise HTTPException(status_code=409, detail="Email already exists")

        conn.execute(
            "UPDATE contacts SET name=?, email=?, phone=?, company=? WHERE id=?",
            (contact.name, contact.email, contact.phone, contact.company, id)
        )
        conn.commit()

        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (id,)).fetchone()
        return row_to_contact(row)


# ---------------------------------------
# DELETE /contacts/{id}
# ---------------------------------------
@app.delete("/contacts/{id}", status_code=204)
def delete_contact(id: int = Path(..., gt=0)):
    with sqlite3.connect(DB_PATH) as conn:
        exists = conn.execute(
            "SELECT 1 FROM contacts WHERE id = ?", (id,)
        ).fetchone()

        if not exists:
            raise HTTPException(status_code=404, detail="Contact not found")

        conn.execute("DELETE FROM contacts WHERE id = ?", (id,))
        conn.commit()

    return None

