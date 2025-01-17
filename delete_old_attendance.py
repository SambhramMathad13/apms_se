import os
import django
from datetime import datetime, timedelta
from django.db import transaction
from emp.models import Attendance  # Replace 'myapp' with your app name

# Initialize Django settings
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aps.settings")  # Replace 'project_name' with your project
# django.setup()

def delete_old_attendance():
    try:
        # Calculate the threshold date (4 months ago)
        threshold_date = datetime.now() - timedelta(days=4 * 30)
        
        # Fetch attendance records older than the threshold
        old_records = Attendance.objects.filter(date__lt=threshold_date)
        total_records = old_records.count()
        
        if total_records == 0:
            print("No old attendance records found.")
            return
        
        # Use a transaction to safely delete records
        with transaction.atomic():
            old_records.delete()
        
        print(f"Successfully deleted {total_records} attendance records older than {threshold_date.date()}.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    delete_old_attendance()
