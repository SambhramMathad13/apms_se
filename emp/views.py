from datetime import datetime, time, timedelta
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from .models import Employee, Attendance, AdvancePayment
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
from datetime import date
from django.conf import settings
SPECIAL_PASSWORD = "admin"
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from django.core.cache import cache





def download_attendance(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            return render(request, "download_attendance.html", {"error": "Please select both start and end dates."})

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return render(request, "download_attendance.html", {"error": "Invalid date format."})

        attendance_records = Attendance.objects.filter(date__range=[start_date, end_date]).select_related("employee")

        if not attendance_records.exists():
            return render(
                request,
                "download_attendance.html",
                {"error": "No attendance records found for the selected date range."},
            )

        # Generate CSV file
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="attendance_{start_date.strftime("%Y%m%d")}to{end_date.strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(["Employee ID", "Employee Name", "Date", "Morning Check-In", "Lunch Check-In", "Lunch Check-Out", "Evening Check-Out"])

        for record in attendance_records.iterator():
            writer.writerow([
                record.employee.id,
                f"{record.employee.first_name} {record.employee.last_name}",
                record.date.strftime("%Y-%m-%d"),
                record.morning_check_in_time.strftime("%H:%M:%S") if record.morning_check_in_time else "N/A",
                record.lunch_check_in_time.strftime("%H:%M:%S") if record.lunch_check_in_time else "N/A",
                record.lunch_check_out_time.strftime("%H:%M:%S") if record.lunch_check_out_time else "N/A",
                record.morning_check_out_time.strftime("%H:%M:%S") if record.morning_check_out_time else "N/A",
            ])

        return response

    return render(request, "download_attendance.html")








# Authentication Views
def admin_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")  # Use username instead of email
        password = request.POST.get("password")

        # Authenticate using Django's User model
        user = authenticate(request, username=username, password=password)
        
        if user is not None:  # Check if the user is authenticated and is an admin
            login(request, user)  # Log in the user
            messages.success(request, "Successfully logged in.")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username, password, or you don't have admin privileges.")
    
    return render(request, "admin_login.html")


def admin_logout(request):
    logout(request)  # Log out the user
    messages.success(request, "Successfully logged out.")
    return redirect("admin_login")


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    # Get today's date
    today = date.today()

    # Define a unique cache key for today's attendance data
    cache_key = "dashboard_attendance"

    # Attempt to get cached data
    cached_data = cache.get(cache_key)

    if cached_data:
        # Extract cached values
        attendance = cached_data['attendance']
        total_employees = cached_data['total_employees']
        employees_in_office = cached_data['employees_in_office']
    else:
        # Base attendance queryset for today's records
        attendance = Attendance.objects.filter(
            Q(morning_check_in_time__isnull=False) |
            Q(lunch_check_in_time__isnull=False),
            date=today
        ).select_related('employee').order_by('employee__id')
        # Count total employees and employees in office
        total_employees = Employee.objects.count()
        employees_in_office = attendance.count()

        # Cache the data for future use
        cache.set(cache_key, {
            'attendance': attendance,
            'total_employees': total_employees,
            'employees_in_office': employees_in_office,
        }, timeout=900)  # Cache for 1 hour (3600 seconds)

    # Get the search query from the request
    search_query = request.GET.get("search", "").strip()

    # Filter attendance records based on the search query
    if search_query:
        attendance = attendance.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__id__icontains=search_query)
        )

    # Paginate the queryset
    page_number = request.GET.get("page", 1)
    paginator = Paginator(attendance, 10)  # Show 10 records per page
    attendance_records = paginator.get_page(page_number)

    return render(request, "dashboard.html", {
        "attendance_records": attendance_records,
        "search_query": search_query,
        "total_employees": total_employees,
        "employees_in_office": employees_in_office,
    })


def all_employees(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect("admin_login")

    # Get search query and page number from the request
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)

    # Check if employees are cached
    employees = cache.get('all_employees')

    if employees is None:
        # Fetch from the database and cache it
        employees = Employee.objects.all().order_by('id')
        cache.set('all_employees', employees,60*30)

    if search_query:
        # Filter employees based on search query
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Implement pagination
    paginator = Paginator(employees, 8)  # Show 8 employees per page
    page_obj = paginator.get_page(page_number)

    # Render the response
    return render(request, 'allemp.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


# Employee Management Views
def add_employee(request):

    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            section = request.POST.get("section")
            address = request.POST.get("address")
            gender = request.POST.get("gender")
            mobile = request.POST.get("mobile")
            base_salary = request.POST.get("base_salary")

            Employee.objects.create(
                first_name=first_name,
                last_name=last_name,
                section=section,
                address=address,
                gender=gender,
                mobile=mobile,
                base_salary=base_salary,
            )
            # Clear the cache for all employees
            cache.delete("all_employees")
            messages.success(request, "Employee added successfully.")
            return redirect("all_employees")

        return render(request, "add_employee.html")
    else:
        return redirect("admin_login")



def edit_employee(request, employee_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect("admin_login")

    # Fetch the employee or return 404 if not found
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == "POST":
        special_password = request.POST.get("special_password", "").strip()

        # Validate the special password
        if special_password == SPECIAL_PASSWORD:
            # Update employee details with data from the POST request
            employee.first_name = request.POST.get("first_name", employee.first_name)
            employee.last_name = request.POST.get("last_name", employee.last_name)
            employee.section = request.POST.get("section", employee.section)
            employee.address = request.POST.get("address", employee.address)
            employee.gender = request.POST.get("gender", employee.gender)
            employee.mobile = request.POST.get("mobile", employee.mobile)
            employee.base_salary = request.POST.get("base_salary", employee.base_salary)
            employee.save()
            # Clear the cache for all employees
            cache.delete("all_employees")
            messages.success(request, "Employee details updated successfully.")
            return redirect("all_employees")
        else:
            messages.error(request, "Incorrect special password. Changes were not saved.")
            return redirect("edit_employee", employee_id=employee_id)

    # Render the edit form
    return render(request, "edit_employee.html", {"employee": employee})

def delete_employee(request, employee_id):
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            special_password = request.POST.get("special_password", "")
            if special_password == SPECIAL_PASSWORD:
                employee = get_object_or_404(Employee, id=employee_id)
                employee.delete()
                # Clear the cache for all employees
                cache.delete("all_employees")
                messages.success(request, "Employee deleted successfully.")
            else:
                messages.error(request, "Incorrect password. Employee not deleted.")
            return redirect("all_employees")
    else:
        return redirect("admin_login")    


def scan_view(request):
    if not request.user.is_authenticated:
        return redirect("admin_login")
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        if employee_id:
            eid=employee_id[4:]
            try:
                employee = get_object_or_404(Employee, id=eid)
            except:
                messages.error(request, "Invalid QR code or employee not found.")
                return render(request, 'scan.html')
            current_time = datetime.now()
            attendance, _ = Attendance.objects.get_or_create(employee=employee, date=current_time.date())

            def time_in_range(start, end, check):
                return start <= check <= end

            current_time_only = current_time.time()
            # print(current_time_only)

            #clear cache
            cache.delete("dashboard_attendance")

            # Morning Check-in
            if time_in_range(time(6, 0), time(10, 59), current_time_only):
                if not attendance.morning_check_in_time:
                    attendance.morning_check_in_time = current_time
                    attendance.save()
                    messages.success(request, f"Morning check-in recorded successfully for {employee.first_name}.")
                else:
                    messages.error(request, f"Morning check-in already recorded for {employee.first_name}.")

            # Late Check-in
            elif time_in_range(time(11, 0), time(12, 29), current_time_only):
                if not attendance.morning_check_in_time:
                    attendance.morning_check_in_time = current_time
                    attendance.save()
                    messages.warning(request, f"Late check-in for {employee.first_name}. Please confirm with admin.")
                else:
                    messages.error(request, f"Morning check-in already recorded for {employee.first_name}.")

            # Lunch Check-in and Check-out
            elif time_in_range(time(12, 30), time(18, 0), current_time_only):
                if not attendance.morning_check_in_time and not attendance.lunch_check_in_time:
                    attendance.lunch_check_in_time = current_time
                    attendance.save()
                    messages.error(request, f"Morning check-in missing for {employee.first_name}. Recording lunch-in instead.")
                elif not attendance.lunch_check_in_time:
                    attendance.lunch_check_in_time = current_time
                    attendance.save()
                    messages.success(request, f"Lunch check-in recorded successfully for {employee.first_name}.")
                elif attendance.lunch_check_in_time and not attendance.lunch_check_out_time:
                    lunch_duration = current_time - attendance.lunch_check_in_time
                    if lunch_duration > timedelta(hours=1):
                        attendance.lunch_check_out_time = current_time
                        attendance.save()
                        messages.warning(request, f"Employee {employee.first_name} is late from lunch. Please confirm with admin.")
                    else:
                        attendance.lunch_check_out_time = current_time
                        attendance.save()
                        messages.success(request, f"Lunch check-out recorded successfully for {employee.first_name}.")
                else:
                    messages.error(request, f"Lunch check-in and check-out already recorded for {employee.first_name}.")

            # Evening Check-out
            elif time_in_range(time(18, 1), time(23, 55), current_time_only):
                if attendance.morning_check_in_time and not attendance.morning_check_out_time:
                    attendance.morning_check_out_time = current_time
                    attendance.save()
                    messages.success(request, f"Evening check-out recorded successfully for {employee.first_name}.")
                elif not attendance.morning_check_in_time and attendance.lunch_check_in_time:
                    attendance.morning_check_out_time = current_time
                    attendance.save()
                    messages.success(request, f"Evening check-out recorded successfully for {employee.first_name}. HALF DAY...")
                elif not attendance.morning_check_in_time:
                    messages.warning(request, f"Employee {employee.first_name} is too late to check in. Please confirm with admin.")
                else:
                    messages.error(request, f"Evening check-out already recorded for {employee.first_name}.")

            # Invalid Check-in/out Time
            else:
                messages.error(request, f"Invalid check-in/out time for {employee.first_name}.")
        else:
            messages.error(request, "No QR code data provided.")
    return render(request, 'scan.html')



# Attendance Viewing View
def view_employee_attendance(request, employee_id):
    if request.user.is_authenticated and request.user.is_superuser:
        # Fetch the employee
        employee = get_object_or_404(Employee, id=employee_id)

        # Get all advances for the employee, ordered by date descending
        advances = AdvancePayment.objects.filter(employee=employee).order_by('-date')

        # Calculate total amounts for 'taken' and 'paid'
        total_taken = advances.filter(type='taken').aggregate(total=Sum('amount'))['total'] or 0
        total_paid = advances.filter(type='paid').aggregate(total=Sum('amount'))['total'] or 0

        # Calculate net
        net = total_taken - total_paid

        # Check if advances exceed 5
        merge = advances.count() > 5

        # Pass data to the template
        return render(request, 'view_employee_attendance.html', {
            'employee': employee,
            'advances': advances,
            'net': net,  # Send net to the template
            'merge': merge,  # Merge flag
        })
    else:
        return redirect("admin_login")


def merge_advances(request, employee_id):
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            # Fetch the employee
            employee = get_object_or_404(Employee, id=employee_id)

            # Get the net amount from the POST data
            net_amount = float(request.POST.get("net", 0))

            # Determine the type based on net_amount
            net_type = 'taken' if net_amount > 0 else 'paid'

            # Get all the advances to merge
            advances_to_merge = AdvancePayment.objects.filter(employee=employee)

            # Delete the old advances
            advances_to_merge.delete()

            current_time = datetime.now()

            # Create a new compressed advance entry
            AdvancePayment.objects.create(
                employee=employee,
                amount=abs(net_amount),
                date=current_time.date(),
                type=net_type
            )


            messages.success(request, "Advances successfully merged.")
            return redirect('view_employee_attendance', employee_id=employee.id)
    else:
        return redirect("admin_login")



# Advance Payment View
def advance_payment(request, employee_id):
    # Check if the user is authenticated and has superuser privileges
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            # Extract form data
            amount = request.POST.get('amount', 0)
            password = request.POST.get('password', '')
            advance_type = request.POST.get('type', 'taken')

            # Check if the provided password matches the special password
            special_password = getattr(settings, 'SPECIAL_PASSWORD', None)
            if not special_password or password != special_password:
                messages.error(request, 'Invalid password...')
                return redirect('view_employee_attendance', employee_id=employee_id)

            # Validate the amount
            try:
                amount = float(amount)
                if amount <= 0:
                    messages.error(request, 'Invalid amount. Please enter a positive number.')
                    return redirect('view_employee_attendance', employee_id=employee_id)
            except ValueError:
                messages.error(request, 'Invalid amount format. Please enter a valid number.')
                return redirect('view_employee_attendance', employee_id=employee_id)

            # Create the advance payment record
            employee = get_object_or_404(Employee, id=employee_id)
            AdvancePayment.objects.create(employee=employee, amount=amount, type=advance_type)

            # Success message
            messages.success(request, 'Advance payment recorded successfully.')
            return redirect('view_employee_attendance', employee_id=employee_id)

        # If the request method is not POST, redirect back with an error message
        messages.error(request, 'Invalid request method.')
        return redirect('view_employee_attendance', employee_id=employee_id)

    # Redirect to admin login if the user is not authenticated
    messages.error(request, 'You must be logged in as an admin to perform this action.')
    return redirect("admin_login")


def calculate_salary(request, employee_id):
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            # Parse data from the request
            data = json.loads(request.body)
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            # Ensure both dates are provided
            if not start_date or not end_date:
                return JsonResponse({'error': 'Start and End dates are required.'}, status=400)

            # Convert strings to date objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get the employee instance
            employee = get_object_or_404(Employee, id=employee_id)

            # Filter attendance records within the date range
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__range=(start_date, end_date)
            ).order_by('-date')

            # Calculate valid workdays
            valid_workdays = attendance_records.filter(
                morning_check_in_time__isnull=False,
                morning_check_out_time__isnull=False
            ).count()

            # Calculate the total salary
            total_salary = (valid_workdays * (employee.base_salary // 30))

            # Return attendance records, advance details, and salary
            return JsonResponse({
                'employee': f'{employee.first_name} {employee.last_name}',
                'attendance_records': [
                    {
                        'date': record.date.strftime('%Y-%m-%d'),
                        'morning_check_in': record.morning_check_in_time.strftime('%H:%M:%S') if record.morning_check_in_time else "Not Checked In",
                        'lunch_check_in': record.lunch_check_in_time.strftime('%H:%M:%S') if record.lunch_check_in_time else "Not Checked In",
                        'lunch_check_out': record.lunch_check_out_time.strftime('%H:%M:%S') if record.lunch_check_out_time else "Not Checked Out",
                        'evening_check_out': record.morning_check_out_time.strftime('%H:%M:%S') if record.morning_check_out_time else "Not Checked Out",
                    }
                    for record in attendance_records
                ],
                'valid_workdays': valid_workdays,
                'total_salary': total_salary
            })
        else:
            return JsonResponse({'error': 'Invalid request method.'}, status=405)
    else:
        return redirect("admin_login")    
