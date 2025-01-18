from django.db import models
from django.utils.timezone import now
import qrcode
from io import BytesIO
from django.core.files import File
import os
from django.db import models
from django.core.files.storage import default_storage
import logging
from PIL import ImageDraw, ImageFont

# Employee Model
logger = logging.getLogger(__name__)

class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    SECTION_CHOICES = [
        ('Billing Section', 'Billing Section'),
        ('Men’s Nicker', 'Men’s Nicker'),
        ('Bag Section', 'Bag Section'),
        ('Saree section', 'Saree section'),
        ('Shirting and Suiting', 'Shirting and Suiting'),
        ('Men’s Readymade', 'Men’s Readymade'),
        ('Parakar', 'Parakar'),
        ('Ladies Undergarments', 'Ladies Undergarments'),
        ('Blouse Pc Section', 'Blouse Pc Section'),
        ('TOP section', 'TOP section'),
        ('Chudi Section', 'Chudi Section'),
        ('Kids Section', 'Kids Section'),
        ('Towel Section', 'Towel Section'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.TextField(blank=True)  # Allow blank values
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    mobile = models.CharField(max_length=11, blank=True)  # Allow blank values
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    section = models.CharField(max_length=50, choices=SECTION_CHOICES)  # New section field
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.section})"

    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if the instance is new (not yet saved)
        super().save(*args, **kwargs)  # Save initially to ensure the instance has an ID

        if is_new:
            try:
                # Generate the QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(f'EMP-{self.id}')
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                # Add employee name below the QR code
                draw = ImageDraw.Draw(img)
                font_size = 20
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

                text = f'{self.first_name}'  # Replace with your field name
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                img_width, img_height = img.size

                # Calculate text position
                text_x = (img_width - text_width) // 2
                text_y = img_height - text_height - 10
                draw.text((text_x, text_y), text, fill="black", font=font)

                # Save the QR code image
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                # Save the QR code file
                self.qr_code.save(f'{self.first_name}_{self.last_name}_{self.id}.png', File(buffer), save=False)
                self.save(update_fields=['qr_code'])

                logger.info(f"QR code successfully generated for EMP-{self.id}")

            except Exception as e:
                logger.error(f"Error generating QR code for EMP-{self.id}: {e}")
                raise


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

class AdvancePayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=now)
    is_paid = models.BooleanField(default=False)  # New boolean field

    def __str__(self):
        return f"{self.employee} - {self.amount} - {'Paid' if self.is_paid else 'Unpaid'}"
