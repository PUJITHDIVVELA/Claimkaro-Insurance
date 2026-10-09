from database.connection import get_db_connection
from utils.helpers import generate_claim_number, log_audit
from datetime import datetime

class ClaimService:
    @staticmethod
    def submit_claim(customer_id, policy_id, reason, description, claim_amount, claim_date, document_info=None):
        if not reason or not description or not claim_amount or not claim_date:
            return False, "All required claim fields must be filled.", None

        try:
            claim_amount = float(claim_amount)
            if claim_amount <= 0:
                return False, "Claim amount must be greater than zero.", None
        except ValueError:
            return False, "Invalid claim amount.", None

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Verify policy belongs to customer and is ACTIVE
                cursor.execute("""
                    SELECT p.*, pt.name as policy_type_name
                    FROM policies p
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    WHERE p.id = %s AND p.customer_id = %s
                """, (policy_id, customer_id))
                pol = cursor.fetchone()
                if not pol:
                    return False, "Invalid policy or policy does not belong to you.", None

                if pol['status'] != 'ACTIVE':
                    return False, f"Claims cannot be submitted for a policy with status '{pol['status']}'.", None

                if claim_amount > float(pol['coverage_amount']):
                    return False, f"Claim amount (Rs {claim_amount:,.2f}) exceeds policy coverage (Rs {pol['coverage_amount']:,.2f}).", None

                # Generate Claim Number
                claim_num = generate_claim_number()

                # Assign an available Claims Officer (or default to officer with fewest claims)
                cursor.execute("""
                    SELECT id FROM users WHERE role = 'CLAIMS_OFFICER' AND status = 'ACTIVE' LIMIT 1
                """)
                officer = cursor.fetchone()
                officer_id = officer['id'] if officer else None

                cursor.execute("""
                    INSERT INTO claims (claim_number, policy_id, customer_id, reason, description, claim_amount, claim_date, status, assigned_officer_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'SUBMITTED', %s)
                """, (claim_num, policy_id, customer_id, reason, description, claim_amount, claim_date, officer_id))
                claim_id = cursor.lastrowid

                # Save document record if uploaded
                if document_info:
                    cursor.execute("""
                        INSERT INTO claim_documents (claim_id, file_name, file_path, file_type, file_size, uploaded_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (claim_id, document_info['original_name'], document_info['file_path'],
                          document_info['file_type'], document_info['file_size'], customer_id))

                # Create Notification
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type)
                    VALUES (%s, %s, %s, 'INFO')
                """, (customer_id, "Claim Submitted", f"Claim {claim_num} for Rs {claim_amount:,.2f} has been submitted successfully and is under processing."))

            log_audit(customer_id, "CLAIM_SUBMIT", "CLAIM", f"Submitted claim {claim_num}")
            return True, f"Claim submitted successfully! Claim Number: {claim_num}", {"claim_id": claim_id, "claim_number": claim_num}
        except Exception as e:
            return False, f"Claim submission failed: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def get_customer_claims(customer_id, search="", status_filter=""):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT c.*, p.policy_number, pt.name as policy_type_name,
                           off.name as officer_name
                    FROM claims c
                    JOIN policies p ON c.policy_id = p.id
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    LEFT JOIN users off ON c.assigned_officer_id = off.id
                    WHERE c.customer_id = %s
                """
                params = [customer_id]

                if search:
                    query += " AND (c.claim_number LIKE %s OR p.policy_number LIKE %s OR c.reason LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
                if status_filter:
                    query += " AND c.status = %s"
                    params.append(status_filter)

                query += " ORDER BY c.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_claim_details(claim_id, user_id=None, role='CUSTOMER'):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT c.*, p.policy_number, p.coverage_amount, p.start_date, p.end_date,
                           pt.name as policy_type_name,
                           cust.name as customer_name, cust.email as customer_email, cust.phone as customer_phone,
                           cp.address as customer_address, cp.city as customer_city,
                           off.name as officer_name, off.email as officer_email
                    FROM claims c
                    JOIN policies p ON c.policy_id = p.id
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    JOIN users cust ON c.customer_id = cust.id
                    LEFT JOIN customer_profiles cp ON cust.id = cp.user_id
                    LEFT JOIN users off ON c.assigned_officer_id = off.id
                    WHERE c.id = %s
                """
                cursor.execute(query, (claim_id,))
                claim = cursor.fetchone()

                if not claim:
                    return None

                # Security check
                if role == 'CUSTOMER' and claim['customer_id'] != user_id:
                    return None

                # Fetch claim documents
                cursor.execute("""
                    SELECT cd.*, u.name as uploader_name
                    FROM claim_documents cd
                    JOIN users u ON cd.uploaded_by = u.id
                    WHERE cd.claim_id = %s
                    ORDER BY cd.uploaded_at DESC
                """, (claim_id,))
                documents = cursor.fetchall()

                # Fetch claim reviews history
                cursor.execute("""
                    SELECT cr.*, off.name as officer_name
                    FROM claim_reviews cr
                    JOIN users off ON cr.officer_id = off.id
                    WHERE cr.claim_id = %s
                    ORDER BY cr.review_date DESC
                """, (claim_id,))
                reviews = cursor.fetchall()

                claim['documents'] = documents
                claim['reviews'] = reviews
                return claim
        finally:
            conn.close()

    @staticmethod
    def review_claim(claim_id, officer_id, decision, remarks=""):
        if decision not in ['APPROVED', 'REJECTED', 'REQUEST_MORE_DOCUMENTS', 'UNDER_REVIEW']:
            return False, "Invalid decision choice."

        if decision == 'REJECTED' and not remarks.strip():
            return False, "A clear reason is required when rejecting a claim."

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
                claim = cursor.fetchone()
                if not claim:
                    return False, "Claim not found."

                # Determine new claim status
                new_status = 'UNDER_REVIEW'
                if decision == 'APPROVED':
                    new_status = 'APPROVED'
                elif decision == 'REJECTED':
                    new_status = 'REJECTED'
                elif decision == 'REQUEST_MORE_DOCUMENTS':
                    new_status = 'DOCUMENT_REQUIRED'
                elif decision == 'UNDER_REVIEW':
                    new_status = 'UNDER_REVIEW'

                # Record review
                cursor.execute("""
                    INSERT INTO claim_reviews (claim_id, officer_id, decision, remarks)
                    VALUES (%s, %s, %s, %s)
                """, (claim_id, officer_id, decision if decision != 'UNDER_REVIEW' else 'REQUEST_MORE_DOCUMENTS', remarks))

                # Update claim status
                cursor.execute("""
                    UPDATE claims SET status = %s, assigned_officer_id = %s WHERE id = %s
                """, (new_status, officer_id, claim_id))

                # Send notification to customer
                notif_msg = f"Your claim {claim['claim_number']} status has been updated to '{new_status}'."
                if remarks:
                    notif_msg += f" Remarks: {remarks}"
                
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type)
                    VALUES (%s, %s, %s, %s)
                """, (claim['customer_id'], f"Claim Status Update: {claim['claim_number']}", notif_msg,
                      'SUCCESS' if decision == 'APPROVED' else 'WARNING' if decision == 'REJECTED' else 'INFO'))

            log_audit(officer_id, "CLAIM_REVIEW", "CLAIM", f"Reviewed claim {claim['claim_number']} with decision {decision}")
            return True, f"Claim status updated to {new_status}."
        except Exception as e:
            return False, f"Failed to review claim: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_officer_claims(officer_id=None, status_filter="", search=""):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT c.*, p.policy_number, pt.name as policy_type_name,
                           cust.name as customer_name, cust.email as customer_email,
                           off.name as officer_name
                    FROM claims c
                    JOIN policies p ON c.policy_id = p.id
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    JOIN users cust ON c.customer_id = cust.id
                    LEFT JOIN users off ON c.assigned_officer_id = off.id
                    WHERE 1=1
                """
                params = []

                if status_filter:
                    query += " AND c.status = %s"
                    params.append(status_filter)

                if search:
                    query += " AND (c.claim_number LIKE %s OR cust.name LIKE %s OR p.policy_number LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

                query += " ORDER BY c.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def upload_document(claim_id, uploader_id, doc_info):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
                claim = cursor.fetchone()
                if not claim:
                    return False, "Claim not found."

                cursor.execute("""
                    INSERT INTO claim_documents (claim_id, file_name, file_path, file_type, file_size, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (claim_id, doc_info['original_name'], doc_info['file_path'], doc_info['file_type'], doc_info['file_size'], uploader_id))

                # If claim was waiting for documents, update to SUBMITTED / UNDER_REVIEW
                if claim['status'] == 'DOCUMENT_REQUIRED':
                    cursor.execute("UPDATE claims SET status = 'UNDER_REVIEW' WHERE id = %s", (claim_id,))

            log_audit(uploader_id, "UPLOAD_DOC", "CLAIM", f"Uploaded document {doc_info['original_name']} for claim {claim['claim_number']}")
            return True, "Document uploaded successfully."
        except Exception as e:
            return False, f"Failed to save document: {str(e)}"
        finally:
            conn.close()
