import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from hotels.models import Organization, Property, RoomType, Room, Guest, Booking


class Command(BaseCommand):
    help = "Seed realistic booking data for performance testing"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20_000)

    def handle(self, *args, **options):
        count = options["count"]

        org, _ = Organization.objects.get_or_create(name="Load Test Chain", slug="load-test-chain")
        prop, _ = Property.objects.get_or_create(
            organization=org, name="Load Test Hotel", defaults={"address": "x", "city": "x", "country": "x"}
        )
        room_type, _ = RoomType.objects.get_or_create(
            property=prop, name="Standard", defaults={"base_price_per_night": 100, "max_occupancy": 2}
        )

        rooms = list(Room.objects.filter(room_type=room_type))
        if len(rooms) < 20:
            for i in range(20 - len(rooms)):
                rooms.append(Room.objects.create(room_type=room_type, room_number=f"LT-{i}"))

        guests = [Guest.objects.create(full_name=f"Load Guest {i}", email=f"load{i}@test.com") for i in range(50)]

        statuses = ["confirmed", "checked_in", "checked_out", "cancelled"]
        start_date = date(2026, 1, 1)
        batch = []

        for i in range(count):
            check_in = start_date + timedelta(days=random.randint(0, 700))
            check_out = check_in + timedelta(days=random.randint(1, 7))
            batch.append(Booking(
                room=random.choice(rooms),
                guest=random.choice(guests),
                check_in=check_in,
                check_out=check_out,
                status=random.choice(statuses),
                total_price=random.randint(80, 500),
            ))
            if len(batch) >= 2000:
                Booking.objects.bulk_create(batch)
                batch = []
                self.stdout.write(f"Inserted {i+1}/{count}")

        if batch:
            Booking.objects.bulk_create(batch)

        self.stdout.write(self.style.SUCCESS(f"Done. Seeded {count} bookings across {len(rooms)} rooms."))