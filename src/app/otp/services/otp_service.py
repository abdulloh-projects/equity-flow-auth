import random

import requests
from django.conf import settings
from django.utils import timezone

from ..models import OTP


class OTPService:
    def __init__(self, email: str, otp: str = None) -> None:
        self.email = email
        self.otp = otp

    def generate_otp(self) -> str:
        otp = str(random.randint(100000, 999999))
        return otp

    def send_otp(self) -> None:
        otp = self.generate_otp()
        otp_record, _ = OTP.objects.update_or_create(
            email=self.email,
            defaults={
                "otp": otp,
                "expires_at": timezone.now() + timezone.timedelta(minutes=5),
                "is_verified": False,
            },
        )
        message = f"Your OTP is: {otp_record.otp}. It will expire in 5 minutes."

        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT}/sendMessage"
            payload = {"chat_id": settings.TELEGRAM_GROUP_ID, "text": message}
            requests.post(url, json=payload)
            return True
        except Exception as e:
            print(f"Error sending OTP: {e}")
            return False

    def verify_otp(self) -> bool:
        try:
            otp_record = OTP.objects.get(email=self.email)
            if otp_record.is_valid() and not otp_record.is_verified:
                if otp_record.otp == self.otp:
                    otp_record.is_verified = True
                    otp_record.save()
                    return True
                return False
            return False
        except OTP.DoesNotExist:
            return False

    def check_otp(self) -> bool:
        try:
            otp_record = OTP.objects.get(email=self.email)
            otp_record.delete()
            return True
        except OTP.DoesNotExist:
            return False
