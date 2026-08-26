from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, Guest


class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ["full_name", "email", "phone"]


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["room", "check_in", "check_out", "total_price"]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if not (room and check_in and check_out):
            return cleaned_data  # let individual field validation report the missing ones

        if check_out <= check_in:
            raise ValidationError("Check-out date must be after check-in date.")

        exclude_id = self.instance.pk if self.instance else None
        if not room.is_available(check_in, check_out, exclude_booking_id=exclude_id):
            raise ValidationError(
                f"Room {room.room_number} is not available for the selected dates."
            )

        return cleaned_data