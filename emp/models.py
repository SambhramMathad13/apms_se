from django.db import models
from django.utils.timezone import now
import qrcode
from io import BytesIO
from django.core.files import File
import os
from django.db import models
from django.core.files.storage import default_storage

# Employee Model

class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.TextField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    mobile = models.CharField(max_length=15, unique=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if the instance is new (not yet saved)
        super().save(*args, **kwargs)  # Save initially to ensure the instance has an ID

        if is_new:  # Generate QR code only for new instances
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f'EMP-{self.id}')
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)

            # Save the QR code file
            self.qr_code.save(f'qr_code_{self.id}.png', File(buffer), save=False)
            self.save(update_fields=['qr_code'])  # Save again to persist the QR code
    def delete(self, *args, **kwargs):
        # Delete the associated QR code file if it exists
        if self.qr_code and default_storage.exists(self.qr_code.path):
            os.remove(self.qr_code.path)

        # Call the parent class delete method
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"            


# Attendance Model
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    morning_check_in_time = models.DateTimeField(null=True, blank=True)
    morning_check_out_time = models.DateTimeField(null=True, blank=True)
    lunch_check_in_time = models.DateTimeField(null=True, blank=True)
    lunch_check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(default=now)

    def __str__(self):
        return f'{self.employee.first_name} {self.employee.last_name} - {self.date}'

# Advance Payments
class AdvancePayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=now)
