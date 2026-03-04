from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    name = models.CharField(max_length = 30)
    age  = models.IntegerField()
    address = models.CharField(max_length = 200)
    duration = models.IntegerField()
    gender = models.CharField(max_length = 10)
    phone = models.CharField(max_length = 100, default = True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Hostel_owner(models.Model):
    name = models.CharField(max_length =200)
    address = models.CharField(max_length =200)
    phone = models.CharField(max_length = 20)
    location = models.CharField(max_length =200)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name       

class Role(models.Model):
    name = models.CharField(max_length = 100)
    description = models.CharField(max_length = 200)

    def __str__(self):
        return self.name


class Administrator(models.Model):
    name = models.CharField(max_length = 200)
    role = models.ForeignKey(Role, on_delete = models.CASCADE, null = True, blank = True)
    phone = models.CharField(max_length =200)


    def __str__(self):
        return self.name


class Hostel(models.Model):
    name = models.CharField(max_length =200)
    hostel_owner = models.ForeignKey(Hostel_owner, on_delete = models.CASCADE, null = True, blank = True)
    location = models.CharField(max_length = 100)
    performance = models.CharField(max_length =100, default = 'Good')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Pending payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    room = models.ForeignKey(Hostel, on_delete = models.CASCADE)
    name = models.ForeignKey(Student, on_delete = models.CASCADE)
    duration = models.CharField(max_length=100, default = 'Pending')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
    booking_date = models.DateField(auto_now_add = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='one_booking_per_student'),
            models.UniqueConstraint(fields=['room'], name='one_booking_per_room'),
        ]

    def __str__(self):
        return f"{self.room.name} booked by {self.name.name}"


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.CharField(max_length=100)
    paid_by_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking.room.name} by {self.booking.name.name}"


class Comments(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.name} - {self.email}"

class Registers(models.Model): 
    full_name = models.CharField(max_length = 100)
    email = models.EmailField(max_length =100)
    password =models.CharField(max_length = 100) 

    def __str__(self):
        return f"Message from {self.name}"      


# Create your models here.


# Create your models here.
