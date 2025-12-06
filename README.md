# Event Registration Portal 

The **Event Registration Portal** is a full-stack **Flask-based web application** designed to **digitize and automate the complete event management process** for educational institutions and organizations. This platform provides an intuitive experience for **students and participants** while delivering powerful **admin management tools** for organizers.

The system supports:

* Secure user authentication
* Dynamic event listings
* Real-time registration tracking
* Online results publishing
* Automated certificate generation in PDF format

With a lightweight architecture, role-based access control, and automated workflows, this system significantly reduces **manual work, paperwork, and operational complexity**.

##  Key Features

###  User Authentication & Role Management

* Secure login system with **role-based access**
* **Admin privileges:**

  * Create & manage events
  * Approve/reject registrations
  * Upload results
  * Generate certificates
* **User privileges:**

  * Register for events
  * View results
  * Download certificates
* Passwords secured using **hashing**
* Session management ensures **authorized access only**

---

###  Event Management System

* Admin can:

  * Create new events
  * Update existing events
  * Delete events
* Users can:

  * View all available events
  * Register instantly
* Backend validation prevents **duplicate registrations**

---

### 📝 Participant Registration & Approval Workflow

* Users submit **online registration forms**
* Admin reviews and **approves/rejects** requests
* Registration status updates **in real time**
* Participant can track their approval status

---

### 🏆 Result Upload & Publishing

* Admin uploads:

  * Scores
  * Ranks
  * Positions
* Results stored securely in the database
* Participants can view results directly on their dashboard
* Ensures **transparent evaluation**

---

### 📜 Certificate Generation (PDF)

* Automated PDF certificate generation using **ReportLab**
* Certificates include:

  * Participant name
  * Event name
  * Performance/position
* Instantly downloadable from user dashboard

---

### 🗄️ Database Integration (SQLite – Expandable)

* Uses **SQLite** for local development
* Database tables:

  * Users
  * Events
  * Registrations
  * Results
  * Certificates
* Schema is designed for **easy migration to MySQL/PostgreSQL**

---

### 🧱 Clean Modular Codebase

* Structured Flask architecture:

  * Routes
  * Templates
  * Static files
  * Database operations
* Reusable CRUD operations
* Validation handled via separate functions
* Dynamic HTML rendering with **Jinja2**

---

### 💻 Responsive Frontend Interface

* Built using:

  * HTML
  * CSS
  * Bootstrap-like styling
  * Jinja2 Templates
* Clean and user-friendly layouts for:

  * Event listing
  * Registration forms
  * Admin dashboard
  * Results & certificate pages

---

### ✅ Error Handling & Data Validation

* Prevents:

  * Duplicate registrations
  * Invalid login attempts
  * Empty form submissions
* Graceful error messages for better user experience

---

## 🛠️ Tech Stack

* **Frontend:** HTML, CSS, Jinja2 Templates
* **Backend:** Python, Flask
* **Database:** SQLite
* **PDF Generation:** ReportLab
* **Authentication:** Session-based with hashed passwords

---

## 🎯 Project Objective

To provide a **complete end-to-end digital event management solution** that:

* Automates registrations
* Eliminates paperwork
* Secures user data
* Simplifies result publishing
* Enables instant certificate generation


