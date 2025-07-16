# 🏛️ Online Chatbot-Based Ticketing System

An AI-powered web-based ticket booking platform designed for museums and cultural institutions. The system leverages a conversational chatbot interface for seamless ticket booking, real-time payment processing, and user engagement.

---

## 📌 Features

- 💬 **Chatbot Integration** – Natural language interface for user queries and ticket booking.
- 🎟️ **Ticket Management** – Book, view, and delete museum tickets.
- 🔒 **User Authentication** – Secure registration and login system.
- 💳 **Stripe Payment Gateway** – Seamless and secure online payments.
- 🧾 **QR Code + PDF Tickets** – Auto-generated digital tickets for entry.
- 🌍 **Multilingual Support** – Language switching with Flask-Babel.
- 📧 **Email Reminders** – Scheduled reminders for upcoming visits.
- 📊 **Admin Dashboard** – View tickets, users, and booking statistics.

---

## 🛠️ Tech Stack

| Layer         | Technology                           |
|--------------|---------------------------------------|
| Frontend      | HTML, CSS, JS, Jinja2                |
| Backend       | Python (Flask Framework)             |
| Chatbot       | Custom Python Logic (Regex-based)    |
| Database      | MySQL (SQLAlchemy ORM)               |
| Payments      | Stripe API                           |
| Scheduling    | APScheduler                          |
| Email Service | Gmail SMTP + smtplib                 |
| Localization  | Flask-Babel                          |
| PDF & QR      | `reportlab`, `qrcode` Python libs    |

---

## 📂 Project Structure

