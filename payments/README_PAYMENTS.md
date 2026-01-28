# Razorpay Payment & Subscription Architecture

This document explains the technical design and reliability strategies of the BookShelf payment system.

## 🏗 Architecture Overview

The system is designed for **extreme reliability**, ensuring that no payment goes unhandled even if there are network failures or server crashes.

### 💰 Components
1.  **Razorpay Sandbox**: Used for payment processing in a safe environment.
2.  **Webhooks (Primary)**: Real-time, server-to-server notifications from Razorpay.
3.  **Polling Job (Secondary/Fallback)**: A Celery task that reconciles "stuck" payments by querying the Razorpay API.
4.  **Celery + Redis**: Handles all background processing asynchronously.

---

## 🚦 Payment State Machine

Every payment moves through a well-defined state machine to prevent accidental access:

1.  **`CREATED`**: The local `Payment` object and Razorpay Order are created.
2.  **`PAID`**: (Internal/polling state) We know the user has paid, but verification is still in progress.
3.  **`VERIFIED`**: The Razorpay signature has been validated (either via Webhook or Polling).
4.  **`ACTIVATED`**: The tenant has been upgraded to PREMIUM, and the subscription is ACTIVE.

---

## 🛡 Reliability Strategies

### 1. Webhooks vs. Polling
- **Webhooks** are the preferred source of truth because they are pushed by Razorpay immediately after an event. 
- **Polling** (via `reconcile_payments_task`) exists for **reconciliation**. If a webhook is missed (due to a server restart or ngrok failure), the polling job will "catch" the payment within 15 minutes by checking its status directly with Razorpay.

### 2. Idempotency & Safety
- **Event Logging**: Every webhook is logged in the `webhook_events` table before processing.
- **Double-Process Prevention**: The system checks if an `event_id` has already been processed before doing any work.
- **Atomic Transactions**: Subscription activation and tenant upgrades happen inside a `transaction.atomic()` block. If any part fails, everything rolls back.

### 3. Lifetime Enforcement
- The `Subscription` model has a `OneToOne` relationship with the `Tenant`.
- Once a subscription is `ACTIVE`, the `CreateOrderView` will strictly block any further payment attempts for that tenant.

---

## 🧪 Testing the Flow

1.  **Frontend**: Navigate to `/api/v1/payments/checkout/`.
2.  **Execution**: Click "Pay with Razorpay", enter test card details.
3.  **Verification**: After payment, wait a few seconds for the background Celery task to finish. Your `Tenant` will automatically upgrade to `PREMIUM`.
