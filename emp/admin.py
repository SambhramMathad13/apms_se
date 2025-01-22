from django.contrib import admin
from .models import Employee, Attendance, AdvancePayment


# Register Attendance model
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'morning_check_in_time', 'morning_check_out_time', 'lunch_check_in_time', 'lunch_check_out_time')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('date',)
    ordering = ('-date',)

# Register Employee model
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id','first_name', 'last_name','section','gender', 'mobile','address', 'base_salary')
    search_fields = ('first_name', 'last_name', 'mobile')
    list_filter = ('gender',)
    ordering = ('first_name',)

# Register AdvancePayment model
@admin.register(AdvancePayment)
class AdvancePaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'date','is_paid')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('date',)
    ordering = ('-date',)
