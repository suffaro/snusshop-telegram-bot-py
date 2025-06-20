# Telegram Snus Reservation System (Deprecated)

> ⚠️ **Note:** This project is deprecated and no longer maintained.

## Overview

This system consists of two main components: a **Telegram bot** and a **Django (or similar) web application**. It is designed to manage snus reservations, handle user interactions, and provide admin-level control over inventory and orders.

---

## 📱 Telegram Bot

### Functionality
- 📇 Manage user contacts
- 🧃 Select a snus product
- 🔢 Choose quantity
- ✅ Confirm and respond that the item is reserved
- ❌ Cancel an existing reservation
- 📋 Display menu buttons
- 📝 Log all user actions
- ⭐ (Optional) Implement a rating system

---

## 🌐 Django App (or Alternative Framework)

### Functionality
- 📖 View all reservations
- ✅ Confirm or ❌ delete reservations
- ➕ Add new items or ➖ remove existing ones
- 💲 Change item prices
- 🔄 Update item availability
- 💬 Open a chat interface with users
- 🗃️ Choose between a database or XLSX-based data storage
- 💰 (Optional) Enable money tracking features

---

## 🗃️ Database Schema

### Tables
- `reservations` – Stores all booking information
- `items` – Snus product details
- `payments` – Transaction records
- `messages` – Message history between users and admin
- `ratings` – User feedback and ratings (optional)

---

## 🚫 Deprecated

This codebase is no longer actively developed. Use at your own discretion.
