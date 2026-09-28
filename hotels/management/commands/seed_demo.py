from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hotels.models import Organization, Property, RoomType, Room, Membership


class Command(BaseCommand):
    help = "Seed a handful of realistic demo properties, room types, and rooms."

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, default="root",
                             help="Give this user Membership at all seeded properties")

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No user named '{username}' — create one first."))
            return

        org, _ = Organization.objects.get_or_create(name="Meridian Hotels", slug="meridian-hotels")

        properties_data = [
            {
                "name": "Meridian Bayfront",
                "address": "12 Harbour Walk",
                "city": "Mumbai",
                "country": "India",
                "room_types": [
                    {"name": "Deluxe King", "description": "Spacious room with harbour views and a king bed.", "price": 145, "occupancy": 2},
                    {"name": "Executive Suite", "description": "Separate living area, premium furnishings, city skyline view.", "price": 260, "occupancy": 3},
                ],
            },
            {
                "name": "Meridian Old Town",
                "address": "45 Heritage Lane",
                "city": "Jaipur",
                "country": "India",
                "room_types": [
                    {"name": "Heritage Room", "description": "Traditional decor with hand-carved furniture, courtyard view.", "price": 95, "occupancy": 2},
                    {"name": "Royal Suite", "description": "Palatial suite with a private terrace and plunge pool.", "price": 310, "occupancy": 4},
                ],
            },
            {
                "name": "Meridian Lakeside",
                "address": "7 Lakeview Promenade",
                "city": "Udaipur",
                "country": "India",
                "room_types": [
                    {"name": "Lake View Room", "description": "Floor-to-ceiling windows overlooking the lake.", "price": 130, "occupancy": 2},
                ],
            },
        ]

        for prop_data in properties_data:
            prop, created = Property.objects.get_or_create(
                organization=org,
                name=prop_data["name"],
                defaults={
                    "address": prop_data["address"],
                    "city": prop_data["city"],
                    "country": prop_data["country"],
                    "created_by": user,
                },
            )

            

            for rt_data in prop_data["room_types"]:
                room_type, _ = RoomType.objects.get_or_create(
                    property=prop,
                    name=rt_data["name"],
                    defaults={
                        "description": rt_data["description"],
                        "base_price_per_night": rt_data["price"],
                        "max_occupancy": rt_data["occupancy"],
                    },
                )
                for i in range(1, 6):  # 5 rooms per room type
                    Room.objects.get_or_create(
                        room_type=room_type,
                        room_number=f"{room_type.name[:1]}{i:02d}",
                    )

            self.stdout.write(self.style.SUCCESS(f"Seeded: {prop.name}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. '{username}' now has Membership at all 3 properties."))