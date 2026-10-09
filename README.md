# ClaimKaro - Enterprise Insurance Policy & Claims Management Platform

ClaimKaro is a production-style **Insurance Policy & Claims Management Web Application** designed with a modern enterprise architecture. Built with **Python Flask (REST APIs)**, **MySQL**, and a responsive **HTML5/CSS3/JavaScript (Bootstrap 5)** frontend.

---

## 🌟 Key Features

- **Role-Based Access Control (RBAC)**: Distinct workflows for `ADMIN`, `CUSTOMER`, `AGENT`, and `CLAIMS_OFFICER`.
- **Policy Management**: Browse insurance plans, enroll in coverage, view active policy limits, and manage policy expiration alerts.
- **Claims Management**: Submit claims against active policies, upload supporting documents (PDF/JPG/PNG), track live visual progress timelines, and manage officer reviews.
- **Claims Assessment**: Claims Officers can inspect claim proofs, verify coverage limits, add official review remarks, and record decisions (`APPROVED`, `REJECTED`, `REQUEST_MORE_DOCUMENTS`).
- **Support Ticket System**: Inbuilt customer support ticket portal with real-time ticket chat messaging between customers and agents.
- **AI Insurance Chatbot**: Floating chatbot widget integrating real-time database lookups for claim status, policy inquiries, and guided **automatic ticket creation** stored directly in MySQL.
- **Notification Engine**: In-app notifications for policy purchases, claim status changes, document requests, and automatic policy expiry alerts (30, 7, 1 day warnings).
- **Admin Control Center**: System metrics dashboard, dynamic Chart.js analytics (Claims distribution, Policy type adoption, Approval rate), User Status management, Policy Type creator, and Audit Log compliance trail.

---

## 🛠 Technology Stack

- **Backend**: Python 3.10+, Flask, Flask-CORS, PyMySQL, Werkzeug (Password Hashing), Python-Dotenv
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, Vanilla JavaScript (ES6+), CSS3, Bootstrap 5, Font Awesome 6, Chart.js
- **API Format**: JSON RESTful APIs

---

## 🗄 Database Configuration

The application automatically creates and initializes the MySQL database on startup.

```python
host = "localhost"
user = "root"
password = "Abhi@123"
database = "insurance_management"
```

### Database Tables (15 Tables)
1. `users` - User accounts & authentication
2. `customer_profiles` - Customer demographics & address
3. `agent_profiles` - Insurance agent credentials
4. `claims_officer_profiles` - Claims assessment officer department info
5. `policy_types` - Insurance products & pricing
6. `policies` - Issued customer policy subscriptions
7. `claims` - Claims applications
8. `claim_documents` - Uploaded claim proofs (PDF/PNG/JPG)
9. `claim_reviews` - Audit trail of officer assessment decisions & remarks
10. `support_tickets` - Customer helpdesk tickets
11. `ticket_messages` - Chat messages for support tickets
12. `chatbot_conversations` - AI chatbot user conversations
13. `chatbot_messages` - Bot & user message history
14. `notifications` - User alerts and notifications
15. `audit_logs` - Compliance activity trail

---

## 🔑 Demo Login Credentials

The database comes pre-seeded with sample data for immediate testing:

| Role | Email | Password | Name |
|---|---|---|---|
| **ADMIN** | `admin@insurance.com` | `Admin@123` | System Admin |
| **CUSTOMER** | `ravi@example.com` | `Customer@123` | Ravi Sharma |
| **CUSTOMER** | `priya@example.com` | `Customer@123` | Priya Patel |
| **CLAIMS OFFICER** | `officer.rajesh@insurance.com` | `Officer@123` | Rajesh Kumar |
| **AGENT** | `agent.sunil@insurance.com` | `Agent@123` | Sunil Verma |

---

## 🚀 Installation & How to Run

### 1. Prerequisites
Ensure MySQL Server is running locally on port 3306 with credentials:
`user: root`, `password: Abhi@123`.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Run the seed script to create all tables and populate initial demo data:
```bash
python3 database/seed.py
```

### 4. Launch Application
```bash
python3 app.py
```
Open your browser and navigate to: `http://localhost:5000`

---

## 📡 REST API Endpoint Summary

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/register` | POST | Public | Register customer account |
| `/login` | POST | Public | Authenticate user & start session |
| `/api/policies/types` | GET | Public | Fetch available insurance plans |
| `/api/policies/purchase` | POST | CUSTOMER | Purchase policy |
| `/api/claims/submit` | POST | CUSTOMER | File new claim with document upload |
| `/api/claims/<id>/review` | POST | OFFICER / ADMIN | Record officer decision & remarks |
| `/api/tickets` | POST | CUSTOMER | Create support ticket |
| `/api/tickets/<id>/messages` | POST | ALL | Send message in ticket chat |
| `/api/chatbot/message` | POST | CUSTOMER | Process chatbot query / auto ticket |
| `/admin/api/dashboard-summary` | GET | ADMIN | Fetch admin dashboard analytics |

---

## 📄 License
Enterprise SaaS Application - Developed for Insurance Policy & Claims Operations.
