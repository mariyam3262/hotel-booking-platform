# Hotel Booking & Operations Platform

A Django REST API for multi-property hotel management: availability search,
booking with double-booking prevention, staff role management, and an
AI concierge -- built to demonstrate production backend patterns.

## Architecture decisions

- **Row-level multi-tenancy, scoped to Property, not Organization** -- a
  front-desk worker at one property shouldn't see bookings at another,
  even within the same hotel chain.
- **Three-layer overlap protection**: application-level check (fast, clean
  errors) + select_for_update() row locking (prevents races within Django)
  + a Postgres ExclusionConstraint with GiST index (the real, unbypassable
  safety net at the database level).
- **Celery with dynamic ETA scheduling** for check-in reminders -- computed
  per-booking, not on a fixed recurring schedule like Beat.
- **JWT with refresh rotation + blacklisting**, audit logging on booking
  changes for dispute/accountability tracking.

## Running locally

    docker-compose up --build
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser

## Tech stack

Django, DRF, PostgreSQL, Redis, Celery, JWT auth, Docker