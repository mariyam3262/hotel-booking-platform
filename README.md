# Hotel Management Platform

A full-stack hotel management system for managing properties, rooms, bookings, guest information, staff access, reviews, and AI-powered concierge interactions. This project combines a Django backend with a Vue frontend to model a realistic multi-property hospitality application.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [API Endpoints](#api-endpoints)
- [Local Setup](#local-setup)
- [Environment Requirements](#environment-requirements)
- [Future Improvements](#future-improvements)
- [Summary](#summary)

## Overview

This application represents a hotel chain with multiple properties. Each property contains room types, physical rooms, staff memberships, bookings, guests, payments, and customer reviews. The platform is designed to enforce property-level access control so staff can operate only within the hotels they are assigned to.

The project focuses on practical hospitality workflows, including reservation handling, inventory management, availability checks, and AI-assisted customer support.

## Features

### Property and Room Management

- multi-property organization model
- room categories such as Deluxe, Suite, and Standard
- physical room inventory per property
- property-level staff membership and roles

### Booking System

- create and view guest bookings
- enforce valid check-in and check-out dates
- detect room overlap conflicts
- support booking statuses such as pending, confirmed, checked in, checked out, and cancelled
- protect against double-booking with database constraints and concurrency-safe logic

### Access Control

- property-scoped authentication and authorization
- users can access only the properties they belong to
- role-based property membership model using owner, manager, and front desk roles

### Payments and Audit Logging

- booking payment records
- audit entries for booking changes
- tracking for operational accountability and debugging

### AI and Review Intelligence

- vector-based semantic search for guest reviews
- AI-powered concierge that answers property-specific questions using relevant reviews and room metadata
- embedding-based similarity search using pgvector and Gemini embeddings

### Background Processing

- Celery-based asynchronous tasks for booking reminders and notifications
- delayed check-in reminder scheduling per booking

## Architecture

The project follows a layered architecture:

1. Frontend: Vue application for hotel operations UI
2. API layer: Django REST Framework endpoints
3. Business logic: Django services and validation routines
4. Persistence layer: PostgreSQL database with constraints and indexes
5. Background jobs: Celery + Redis
6. AI layer: Gemini embedding-based semantic matching and concierge context assembly

### Key architectural decisions

- property-level multi-tenancy instead of organization-wide access
- three-layer booking protection:
  - application validation
  - row locking with select_for_update()
  - PostgreSQL exclusion constraints
- JWT authentication with refresh token rotation
- Redis cache for availability results and concierge answers
- AI embeddings stored alongside review records for semantic matching

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Vue.js
- Pinia
- Vue Router
- JWT authentication
- Docker
- pgvector
- Google Gemini embeddings

## Project Structure

```text
HotelManagement/
├── core/                     # Django project settings and URL configuration
├── hotels/                   # Main hotel business app
│   ├── management/           # Data seeding scripts
│   ├── migrations/           # Database migrations
│   ├── templates/            # Legacy HTML templates
│   ├── admin.py             # Django admin registration
│   ├── ai_tasks.py          # AI-related tasks
│   ├── forms.py             # Booking and guest form definitions
│   ├── models.py            # Core domain model
│   ├── permissions.py       # Property-scoped permissions
│   ├── serializers.py      # DRF serializers
│   ├── services.py          # Booking and AI context services
│   ├── signals.py           # App signals
│   ├── tasks.py             # Celery tasks
│   ├── throttles.py        # API throttling rules
│   ├── urls.py             # Hotel app URLs
│   ├── views.py            # API and legacy views
│   └── tests.py            # Tests
├── hotel-frontend/          # Vue frontend project
├── docker-compose.yml       # Local service orchestration
├── Dockerfile               # Backend container definition
├── manage.py                # Django entry point
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
└── celerybeat-schedule      # Celery beat schedule file
```

## Core Modules

### `core/`

Contains the Django project configuration, routing, and core application startup settings.

### `hotels/models.py`

Defines the main schema:

- Organization
- Property
- Membership
- RoomType
- Room
- Guest
- Booking
- Payment
- Review
- AuditLog
- FailedTaskLog

### `hotels/services.py`

Handles transactional booking creation and AI concierge context building. It ensures concurrency-safe room assignment and supports idempotency.

### `hotels/views.py`

Provides:

- HTML views for earlier reference flows
- DRF viewsets for properties, rooms, and bookings
- availability checks with caching
- semantic review search endpoint
- AI concierge endpoints

### `hotels/serializers.py`

Contains validation and serialization logic for guests, rooms, bookings, and memberships.

### `hotels/permissions.py`

Implements property-based authorization checks so users can access only relevant hotel records.

### `hotel-frontend/`

The Vue frontend includes routes for:

- login
- dashboard
- property listing
- property details
- booking creation and detail views
- guest concierge
- property creation
- staff management

## API Endpoints

### Authentication

- `POST /api/token/` — obtain JWT token pair
- `POST /api/token/refresh/` — refresh access token

### Core Resources

- `GET /api/v1/properties/`
- `GET /api/v1/bookings/`
- `GET /api/v1/room-types/`
- `GET /api/v1/rooms/`
- `GET /api/v1/memberships/`

### Availability and AI Features

- `GET /api/v1/availability`
- `POST /api/v1/reviews/search/`
- `POST /api/v1/concierge/ask/`
- `POST /api/v1/concierge/ask/stream/`

## Local Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start services with Docker

```bash
docker-compose up --build
```

### 3. Run database migrations

```bash
docker-compose exec web python manage.py migrate
```

### 4. Create a superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Start the frontend

```bash
cd hotel-frontend
npm install
npm run dev
```

## Environment Requirements

The application depends on:

- PostgreSQL database
- Redis
- Celery worker and scheduler
- Gemini API key for embedding and AI features
- Docker for local orchestration

## Future Improvements

- add user registration and organization onboarding
- add deeper role hierarchies and permissions
- expand analytics and operational reporting
- integrate real payment gateways
- add housekeeping and maintenance workflows
- improve frontend UX and dashboards
- add automated tests for concurrency, validation, and edge cases

## Summary

This project is a practical example of a production-style hospitality platform. It combines hotel operations, secure multi-property access, booking safety, background automation, and AI-powered guest intelligence in a single full-stack application.

It is suitable for learning modern Django architecture, API design, concurrency handling, and AI-integrated application development in a real-world domain.
