from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.db import models
from decimal import Decimal

class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Professor(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="professors")
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    department = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        unique_together = [("school", "first_name", "last_name")]

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.school.name})"

class Student(models.Model):
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=120, blank=True)
    last_name  = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)

    enrollment_date  = models.DateField(default=timezone.now, blank=True)
    expiration_date  = models.DateField(null=True, blank=True)  # auto = enrollment + 90 days
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = [('professor', 'email')]

    def __str__(self):
        name = (self.last_name or '') + (', ' + self.first_name if self.first_name else '')
        return name.strip() or (self.email or 'Student')

    @property
    def school(self):
        return self.professor.school

    def save(self, *args, **kwargs):
        if not self.enrollment_date:
            self.enrollment_date = timezone.now().date()
        if not self.expiration_date and self.enrollment_date:
            self.expiration_date = self.enrollment_date + timedelta(days=90)
        super().save(*args, **kwargs)



class Roster(models.Model):
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE, related_name='rosters')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    source_filename = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # NEW: billing / tracking
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    invoice_sent = models.BooleanField(default=False)

    # students in this class/list
    students = models.ManyToManyField('Student', related_name='rosters', blank=True)

    class Meta:
        ordering = ["-created_at", "name"]
        unique_together = [("professor", "name")]

    def __str__(self):
        return f"{self.name} ({self.professor})"

    @property
    def school(self):
        return self.professor.school

    @property
    def is_active(self) -> bool:
        """Active if the roster has ANY student whose expiration_date is today or later."""
        today = timezone.now().date()
        return self.students.filter(expiration_date__gte=today).exists()
