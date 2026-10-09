from database.connection import get_db_connection
from utils.helpers import log_audit
from werkzeug.security import generate_password_hash

class AdminService:
    @staticmethod
    def get_dashboard_metrics():
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'CUSTOMER'")
                total_customers = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'AGENT'")
                total_agents = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'CLAIMS_OFFICER'")
                total_officers = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM policies")
                total_policies = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM policies WHERE status = 'ACTIVE'")
                active_policies = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM claims")
                total_claims = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM claims WHERE status IN ('SUBMITTED', 'UNDER_REVIEW', 'DOCUMENT_REQUIRED')")
                pending_claims = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM claims WHERE status = 'APPROVED'")
                approved_claims = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM claims WHERE status = 'REJECTED'")
                rejected_claims = cursor.fetchone()['total']

                cursor.execute("SELECT COUNT(*) as total FROM support_tickets WHERE status IN ('OPEN', 'IN_PROGRESS')")
                open_tickets = cursor.fetchone()['total']

                # Charts Data: Claims by status
                cursor.execute("SELECT status, COUNT(*) as count FROM claims GROUP BY status")
                claims_by_status = cursor.fetchall()

                # Charts Data: Policies by Type
                cursor.execute("""
                    SELECT pt.name, COUNT(p.id) as count
                    FROM policy_types pt
                    LEFT JOIN policies p ON pt.id = p.policy_type_id
                    GROUP BY pt.id, pt.name
                """)
                policies_by_type = cursor.fetchall()

                # Approval Rate Calculation
                decided_claims = approved_claims + rejected_claims
                approval_rate = round((approved_claims / decided_claims * 100), 1) if decided_claims > 0 else 100.0

                return {
                    "total_users": total_users,
                    "total_customers": total_customers,
                    "total_agents": total_agents,
                    "total_officers": total_officers,
                    "total_policies": total_policies,
                    "active_policies": active_policies,
                    "total_claims": total_claims,
                    "pending_claims": pending_claims,
                    "approved_claims": approved_claims,
                    "rejected_claims": rejected_claims,
                    "open_tickets": open_tickets,
                    "approval_rate": approval_rate,
                    "claims_by_status": claims_by_status,
                    "policies_by_type": policies_by_type
                }
        finally:
            conn.close()

    @staticmethod
    def get_all_users(role_filter="", status_filter="", search=""):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT u.id, u.name, u.email, u.phone, u.role, u.status, u.created_at,
                           cp.city, cp.state, ap.employee_id as agent_emp, cop.employee_id as officer_emp
                    FROM users u
                    LEFT JOIN customer_profiles cp ON u.id = cp.user_id
                    LEFT JOIN agent_profiles ap ON u.id = ap.user_id
                    LEFT JOIN claims_officer_profiles cop ON u.id = cop.user_id
                    WHERE 1=1
                """
                params = []

                if role_filter:
                    query += " AND u.role = %s"
                    params.append(role_filter)

                if status_filter:
                    query += " AND u.status = %s"
                    params.append(status_filter)

                if search:
                    query += " AND (u.name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

                query += " ORDER BY u.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def update_user_status(admin_id, target_user_id, new_status):
        if new_status not in ['ACTIVE', 'INACTIVE', 'SUSPENDED']:
            return False, "Invalid status choice."
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET status = %s WHERE id = %s", (new_status, target_user_id))
            log_audit(admin_id, "USER_STATUS_UPDATE", "ADMIN", f"Updated user #{target_user_id} status to {new_status}")
            return True, f"User status updated to {new_status}."
        finally:
            conn.close()

    @staticmethod
    def create_policy_type(admin_id, name, description, coverage, premium, duration_months=12):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO policy_types (name, description, coverage, premium, duration_months, status)
                    VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """, (name, description, coverage, premium, duration_months))
                pt_id = cursor.lastrowid
            log_audit(admin_id, "POLICY_TYPE_CREATE", "ADMIN", f"Created policy type '{name}'")
            return True, "Policy type created successfully.", {"id": pt_id}
        finally:
            conn.close()

    @staticmethod
    def get_audit_logs(limit=100):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT al.*, u.name as user_name, u.role as user_role
                    FROM audit_logs al
                    LEFT JOIN users u ON al.user_id = u.id
                    ORDER BY al.created_at DESC
                    LIMIT %s
                """, (limit,))
                return cursor.fetchall()
        finally:
            conn.close()
