from django.db import models
from django.utils.timezone import now

# Create your models here.


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)
    expires_at = models.DateTimeField(default=now)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        return now() < self.expires_at

    def __str__(self):
        return self.email
