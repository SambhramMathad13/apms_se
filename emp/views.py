from datetime import datetime, time, timedelta
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Sum
from .models import Employee, Attendance, AdvancePayment
from django.contrib.auth.models import User  # Import User model
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
from datetime import date

# Authentication Views               add the auth code here also .....
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # Use username instead of email
        password = request.POST.get("password")

        # Authenticate using Django's User model
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:  # Check if the user is authenticated and is an admin
            login(request, user)  # Log in the user
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username, password, or you don't have admin privileges.")
    
    return render(request, "admin_login.html")

def admin_logout(request):
    logout(request)  # Log out the user
    return redirect("admin_login")



def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    # Get today's date
    today = date.today()

    # Query employees matching either condition
    employees = Attendance.objects.filter(
        Q(
            morning_check_in_time__isnull=True,
            lunch_check_in_time__isnull=False
        ) |
        Q(
            morning_check_in_time__isnull=False
        ),
        date=today  # Ensure 'date' is placed after all positional arguments
    ).select_related('employee')

    # If there's a search query, filter further
    search_query = request.GET.get("search", "")
    if search_query:
        employees = employees.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query)
        )

    return render(request, "dashboard.html", {"attendance_records": employees})



def all_employees(request):
    search_query = request.GET.get('search', '')  # Get the search query from the request
    if search_query:
        employees = Employee.objects.filter(
            first_name__icontains=search_query
        ) | Employee.objects.filter(
            last_name__icontains=search_query
        ) | Employee.objects.filter(
            id__icontains=search_query
        )
    else:
        employees = Employee.objects.all()

    return render(request, 'allemp.html', {'employees': employees})

# Employee Management Views
def add_employee(request):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        address = request.POST.get("address")
        gender = request.POST.get("gender")
        mobile = request.POST.get("mobile")
        base_salary = request.POST.get("base_salary")

        Employee.objects.create(
            first_name=first_name,
            last_name=last_name,
            address=address,
            gender=gender,
            mobile=mobile,
            base_salary=base_salary,
        )
        messages.success(request, "Employee added successfully.")
        return redirect("dashboard")

    return render(request, "add_employee.html")


def edit_employee(request, employee_id):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == "POST":
        employee.first_name = request.POST.get("first_name")
        employee.last_name = request.POST.get("last_name")
        employee.address = request.POST.get("address")
        employee.gender = request.POST.get("gender")
        employee.mobile = request.POST.get("mobile")
        employee.base_salary = request.POST.get("base_salary")
        employee.save()
        messages.success(request, "Employee details updated successfully.")
        return redirect("all_employees")

    return render(request, "edit_employee.html", {"employee": employee})


def delete_employee(request, employee_id):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()
    messages.success(request, "Employee deleted successfully.")
    return redirect("dashboard")

















# def record_attendance(request):
#     if not request.user.is_authenticated:
#         return redirect("admin_login")

#     if request.method == "POST":
#         employee_id = request.POST.get("employee_id")
#         if not employee_id:
#             messages.error(request, "No QR code data provided.")
#             return redirect("dashboard")

#         try:
#             employee = get_object_or_404(Employee, id=employee_id)
#         except:
#             messages.error(request, "Invalid QR code or employee not found.")
#             return redirect("dashboard")

#         current_time = now()
#         attendance, _ = Attendance.objects.get_or_create(employee=employee, date=current_time.date())

#         # Helper function to check if time is in range
#         def time_in_range(start, end, check):
#             return start <= check <= end

#         current_time_only = current_time.time()

#         # Morning Check-in
#         if time_in_range(time(6, 0), time(10, 59), current_time_only):
#             if not attendance.morning_check_in_time:
#                 attendance.morning_check_in_time = current_time
#                 attendance.save()
#                 messages.success(request, f"Morning check-in recorded successfully for {employee.first_name}.")
#             else:
#                 messages.error(request, f"Morning check-in already recorded for {employee.first_name}.")
#             return redirect("dashboard")

#         # Late Check-in
#         elif time_in_range(time(11, 0), time(12, 29), current_time_only):
#             messages.warning(request, f"Late check-in for {employee.first_name}. Please confirm with admin.")
#             return redirect("dashboard")

#         # Lunch Check-in and Check-out
#         elif time_in_range(time(12, 30), time(17, 0), current_time_only):
#             if not attendance.morning_check_in_time:
#                 messages.error(request, f"Morning check-in missing for {employee.first_name}. Recording lunch-in instead.")
#             elif not attendance.lunch_check_in_time:
#                 attendance.lunch_check_in_time = current_time
#                 attendance.save()
#                 messages.success(request, f"Lunch check-in recorded successfully for {employee.first_name}.")
#             elif attendance.lunch_check_in_time and not attendance.lunch_check_out_time:
#                 lunch_duration = current_time - attendance.lunch_check_in_time
#                 if lunch_duration > timedelta(hours=1):
#                     messages.warning(request, f"Employee {employee.first_name} is late from lunch. Please confirm with admin.")
#                 else:
#                     attendance.lunch_check_out_time = current_time
#                     attendance.save()
#                     messages.success(request, f"Lunch check-out recorded successfully for {employee.first_name}.")
#             else:
#                 messages.error(request, f"Lunch check-in and check-out already recorded for {employee.first_name}.")
#             return redirect("dashboard")

#         # Evening Check-out
#         elif time_in_range(time(17, 1), time(22, 0), current_time_only):
#             if attendance.morning_check_in_time and not attendance.evening_check_out_time:
#                 attendance.evening_check_out_time = current_time
#                 attendance.save()
#                 messages.success(request, f"Evening check-out recorded successfully for {employee.first_name}.")
#             elif not attendance.morning_check_in_time:
#                 messages.warning(request, f"Employee {employee.first_name} is too late to check in. Please confirm with admin.")
#             else:
#                 messages.error(request, f"Evening check-out already recorded for {employee.first_name}.")
#             return redirect("dashboard")

#         # Invalid Check-in/out Time
#         else:
#             messages.error(request, f"Invalid check-in/out time for {employee.first_name}.")
#             return redirect("dashboard")

#     return render(request, "record_attendance.html")


















def record_attendance(request):
    if not request.user.is_authenticated:
        return redirect("admin_login")

    if request.method == "POST":
        # Assume the QR code contains the employee_id
        qr_code_data = request.POST.get("employee_id")  # Retrieved from the frontend via POST
        if not qr_code_data:
            messages.error(request, "No QR code data provided.")
            return redirect("dashboard")  # Redirect to the dashboard with the error message

        try:
            employee = get_object_or_404(Employee, id=qr_code_data)
        except:
            messages.error(request, "Invalid QR code or employee not found.")
            return redirect("dashboard")  # Redirect to the dashboard with the error message

        current_time = datetime.now()
        print("Current time is:", current_time)
        print("Current date is:", current_time.date())
        attendance, _ = Attendance.objects.get_or_create(employee=employee, date=current_time.date())

        # Check if morning check-in is missing
        if not attendance.morning_check_in_time:
            attendance.morning_check_in_time = current_time
            attendance.save()
            messages.success(request, f"Attendance recorded successfully for Morning Check-in for {employee.first_name}.")
            return redirect("dashboard")  # Redirect to the dashboard with the success message

        # Check if lunch check-in is missing
        elif not attendance.lunch_check_in_time:
            attendance.lunch_check_in_time = current_time
            attendance.save()
            messages.success(request, f"Attendance recorded successfully for Lunch Check-in for {employee.first_name}.")
            return redirect("dashboard")  # Redirect to the dashboard with the success message

        # Check if lunch check-out is missing
        elif attendance.lunch_check_in_time and not attendance.lunch_check_out_time:
            attendance.lunch_check_out_time = current_time
            attendance.save()
            messages.success(request, f"Attendance recorded successfully for Lunch Check-out for {employee.first_name}.")
            return redirect("dashboard")  # Redirect to the dashboard with the success message

        # Check if evening check-out is missing
        elif not attendance.morning_check_out_time:
            attendance.morning_check_out_time = current_time
            attendance.save()
            messages.success(request, f"Attendance recorded successfully for Evening Check-out for {employee.first_name}.")
            return redirect("dashboard")  # Redirect to the dashboard with the success message

        messages.warning(request, f"All attendance records for {employee.first_name} are already completed.")
        return redirect("dashboard")  # Redirect to the dashboard with the warning message

    return render(request, "record_attendance.html")


# Attendance Viewing View
def view_employee_attendance(request, employee_id):
    if not request.user.is_authenticated:
        return redirect("admin_login")
    
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'view_employee_attendance.html', {'employee': employee})


def calculate_salary(request, employee_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

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

        # Calculate advance payments in the date range
        advances = AdvancePayment.objects.filter(
            employee=employee,
            date__range=(start_date, end_date)
        )
        total_advance = advances.aggregate(Sum('amount'))['amount__sum'] or 0

        # Calculate the total salary
        total_salary = (valid_workdays * employee.base_salary) - total_advance

        # Optional: Delete advances after deduction (if required)
        # advances.delete()

        # Return attendance records and salary details
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
            'total_salary': total_salary,
            'advance_paid': total_advance,
        })
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)





# Advance Payment View
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from .models import Employee, AdvancePayment

def advance_payment(request, employee_id):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Handle POST request
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get('amount', 0)
            password = data.get('password', '')

            # Check if the provided password matches the special password
            special_password = getattr(settings, 'SPECIAL_PASSWORD', None)
            if not special_password or password != special_password:
                return JsonResponse({'error': 'Invalid password'}, status=403)

            # Validate the amount
            if int(amount) > 0:
                employee = get_object_or_404(Employee, id=employee_id)
                AdvancePayment.objects.create(employee=employee, amount=amount)
                return JsonResponse({'message': 'Advance payment recorded successfully.'})
            else:
                return JsonResponse({'error': 'Invalid amount'}, status=400)
        except (ValueError, KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request data'}, status=400)

    # If the request method is not POST, return a 405 error
    return JsonResponse({'error': 'Method not allowed'}, status=405)


