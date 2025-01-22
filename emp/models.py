from django.db import models
from django.utils.timezone import now
from django.db import models
import logging

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
    section = models.CharField(max_length=50, choices=SECTION_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.section})"
            

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
