
# 📂 File: helpers/companies.py

import sqlite3

def generate_company_code(company_name, user_id, conn):
    """
    Generate a smart 3-letter company code for a company, no numbers, always 3 letters, unique per user.
    """
    if not company_name:
        return "XXX"

    normalized_name = company_name.strip().lower()
    c = conn.cursor()

    # ✅ Check if company already exists
    c.execute(
        "SELECT company_code FROM companies WHERE lower(company_name) = ? AND user_id = ?", 
        (normalized_name, user_id)
    )
    existing = c.fetchone()
    if existing:
        return existing[0]

    words = normalized_name.split()

    # Basic abbreviation
    code = ''.join(word[0] for word in words).upper()

    if len(code) == 2:
        code += 'C'
    elif len(code) > 3:
        code = code[:3]

    original_code = code

    # Function to check if code exists
    def is_code_taken(code_check):
        c.execute(
            "SELECT id FROM companies WHERE company_code = ? AND user_id = ?", 
            (code_check, user_id)
        )
        return c.fetchone() is not None

    if is_code_taken(code):
        first_word = words[0] if len(words) >= 1 else ''
        last_word = words[-1] if len(words) >= 1 else ''

        code1 = (first_word[:2] + last_word[0]).upper() if len(first_word) >= 2 and len(last_word) >= 1 else None
        code2 = (first_word[0] + last_word[:2]).upper() if len(first_word) >= 1 and len(last_word) >= 2 else None

        if code1 and not is_code_taken(code1) and len(code1) == 3:
            code = code1
        elif code2 and not is_code_taken(code2) and len(code2) == 3:
            code = code2
        else:
            code = "XXX"

    # ✅ Save the new company + code
    c.execute(
        "INSERT INTO companies (user_id, company_name, company_code) VALUES (?, ?, ?)",
        (user_id, company_name.strip(), code)
    )
    conn.commit()

    return code

def get_company_code(company_name, user_id, conn):
    """
    Retrieve an existing company code for a given company and user, if exists.
    """
    if not company_name:
        return None

    normalized_name = company_name.strip().lower()
    c = conn.cursor()

    c.execute(
        "SELECT company_code FROM companies WHERE lower(company_name) = ? AND user_id = ?",
        (normalized_name, user_id)
    )
    result = c.fetchone()

    return result[0] if result else None

def list_all_companies(user_id, conn):
    """
    List all companies and their codes for a given user.
    """
    c = conn.cursor()
    c.execute(
        "SELECT company_name, company_code FROM companies WHERE user_id = ? ORDER BY company_name ASC",
        (user_id,)
    )
    return c.fetchall()

def delete_company(company_name, user_id, conn):
    """
    Delete a company entry for a given user.
    """
    normalized_name = company_name.strip().lower()
    c = conn.cursor()
    c.execute(
        "DELETE FROM companies WHERE lower(company_name) = ? AND user_id = ?",
        (normalized_name, user_id)
    )
    conn.commit()
