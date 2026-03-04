from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.utils import OperationalError
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from management.models import Comments, Hostel, Hostel_owner, Booking, Student, Payment

def Home(request):
    return render(request, './Home.html')


def HostelsList(request):
    hostels_qs = Hostel.objects.select_related('hostel_owner')
    can_view_all_hostels = False

    if request.user.is_authenticated:
        is_owner = Hostel_owner.objects.filter(user=request.user).exists()
        is_admin = request.user.is_staff or request.user.is_superuser
        can_view_all_hostels = is_owner or is_admin

    if can_view_all_hostels:
        hostels = hostels_qs.all()
    else:
        hostels = hostels_qs.filter(is_available=True)

    return render(
        request,
        './Hostels.html',
        {'hostels': hostels, 'can_view_all_hostels': can_view_all_hostels},
    )


def HostelDetail(request, hostel_id):
    hostel = get_object_or_404(Hostel, id=hostel_id)
    existing_booking = Booking.objects.select_related('name').filter(room=hostel).first()
    student = None
    student_booking = None
    payment = None
    is_owner = False
    is_admin = False
    can_view_booking_identity = False

    if request.user.is_authenticated:
        is_owner = Hostel_owner.objects.filter(user=request.user).exists()
        is_admin = request.user.is_staff or request.user.is_superuser
        can_view_booking_identity = is_owner or is_admin
        student = Student.objects.filter(user=request.user).first()
        if student:
            student_booking = Booking.objects.select_related('room').filter(name=student).first()
            if student_booking and student_booking.room_id == hostel.id:
                payment = Payment.objects.filter(booking=student_booking).first()
                can_view_booking_identity = True

    # Students/guests should not access booked-room details they don't own.
    if existing_booking and not can_view_booking_identity:
        messages.error(request, 'This room is already booked.')
        return redirect('hostels')

    if request.method == 'POST':
        action = request.POST.get('action')

        # Only allow logged-in students to book
        if not request.user.is_authenticated:
            messages.error(request, 'Please login as a student to make a booking.')
            return redirect('login')

        try:
            student = Student.objects.filter(user=request.user).first()
        except OperationalError:
            messages.error(request, 'Database not migrated. Run makemigrations and migrate.')
            return redirect('home')

        if not student:
            messages.error(request, 'Only students can make bookings. Please register as a student.')
            return redirect('register')

        student_booking = Booking.objects.select_related('room').filter(name=student).first()

        if action == 'book':
            if student_booking:
                messages.error(
                    request,
                    f'You already booked "{student_booking.room.name}". A student can only have one room booking.',
                )
                return redirect('hostel_detail', hostel_id=hostel.id)

            if not hostel.is_available or existing_booking:
                messages.error(request, 'This room is no longer available.')
                return redirect('hostel_detail', hostel_id=hostel.id)

            duration = request.POST.get('duration') or 'Pending'
            try:
                booking = Booking.objects.create(
                    room=hostel,
                    name=student,
                    duration=duration,
                    status=Booking.STATUS_PENDING_PAYMENT,
                )
                hostel.is_available = False
                hostel.save(update_fields=['is_available'])
            except IntegrityError:
                messages.error(request, 'Booking could not be completed. You may already have a booking.')
                return redirect('hostel_detail', hostel_id=hostel.id)

            return render(request, './BookingSuccess.html', {'hostel': hostel, 'student': student, 'booking': booking})

        if action == 'pay':
            if not student_booking or student_booking.room_id != hostel.id:
                messages.error(request, 'You can only submit payment for your own booking.')
                return redirect('hostel_detail', hostel_id=hostel.id)

            if Payment.objects.filter(booking=student_booking).exists():
                messages.info(request, 'Payment for this booking was already submitted.')
                return redirect('hostel_detail', hostel_id=hostel.id)

            amount = request.POST.get('amount')
            transaction_code = request.POST.get('transaction_code')
            paid_by_phone = request.POST.get('paid_by_phone')

            if not amount or not transaction_code or not paid_by_phone:
                messages.error(request, 'Please fill all payment fields.')
                return redirect('hostel_detail', hostel_id=hostel.id)

            Payment.objects.create(
                booking=student_booking,
                amount=amount,
                transaction_code=transaction_code,
                paid_by_phone=paid_by_phone,
            )
            messages.success(request, 'Payment submitted. The hostel owner can now review it.')
            return redirect('hostel_detail', hostel_id=hostel.id)

    return render(
        request,
        './HostelDetail.html',
        {
            'hostel': hostel,
            'existing_booking': existing_booking,
            'student_booking': student_booking,
            'payment': payment,
            'can_view_booking_identity': can_view_booking_identity,
        },
    )


@login_required(login_url='login')
def PostRoom(request):
    # Only users linked to a Hostel_owner may post rooms
    try:
        owner = Hostel_owner.objects.filter(user=request.user).first()
    except OperationalError:
        messages.error(request, 'Database not migrated. Run makemigrations and migrate.')
        return redirect('home')

    if not owner:
        messages.error(request, 'Only registered hostel owners can post rooms. Register as an owner to continue.')
        return redirect('home')

    if request.method == 'POST':
        hostel_name = request.POST.get('hostel_name')
        hostel_location = request.POST.get('hostel_location')
        Hostel.objects.create(name=hostel_name, hostel_owner=owner, location=hostel_location, is_available=True)
        messages.success(request, 'Hostel posted successfully!')
        return redirect('hostels')

    return render(request, './PostRoom.html')


@login_required(login_url='login')
def OwnerPayments(request):
    owner = Hostel_owner.objects.filter(user=request.user).first()
    if not owner:
        messages.error(request, 'Only hostel owners can access payments.')
        return redirect('home')

    owner_payments = (
        Payment.objects.select_related('booking', 'booking__room', 'booking__name')
        .filter(booking__room__hostel_owner=owner)
        .order_by('-submitted_at')
    )
    return render(request, 'OwnerPayments.html', {'owner': owner, 'owner_payments': owner_payments})


@login_required(login_url='login')
def OwnerDashboard(request):
    owner = Hostel_owner.objects.filter(user=request.user).first()
    if not owner:
        messages.error(request, 'Only hostel owners can access this page.')
        return redirect('home')

    owner_bookings = (
        Booking.objects.select_related('room', 'name', 'room__hostel_owner')
        .filter(room__hostel_owner=owner)
        .order_by('-booking_date')
    )
    owner_payments = Payment.objects.select_related('booking', 'booking__room', 'booking__name').filter(
        booking__room__hostel_owner=owner
    )

    return render(
        request,
        './OwnerDashboard.html',
        {'owner': owner, 'owner_bookings': owner_bookings, 'owner_payments': owner_payments},
    )

def Register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = (request.POST.get('username') or '').strip()
        email = request.POST.get('email')
        role = request.POST.get('role', 'student')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username:
            messages.error(request, 'Username is required!')
            return render(request, './Register.html')
        
        # Validate passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, './Register.html')
        
        # Check if username/email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return render(request, './Register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, './Register.html')
        
        # Create new user and role-specific record
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name
            )
            user.save()

            if role == 'student':
                Student.objects.create(user=user, name=full_name, age=0, address='', duration=0, gender='', phone='')
            elif role == 'owner':
                Hostel_owner.objects.create(user=user, name=full_name, address='', phone='', location='')

            # Auto-authenticate and login the user immediately to avoid login issues
            auth_user = authenticate(request, username=username, password=password)
            if auth_user is not None:
                login(request, auth_user)
                messages.success(request, 'Registration successful — you are now logged in.')
                # If owner, redirect to post-room page, otherwise to hostels
                if role == 'owner':
                    return redirect('post_room')
                return redirect('hostels')

            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, './Register.html')
    
    return render(request, './Register.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password!')
            return render(request, './Login.html')
    
    return render(request, './Login.html')

@login_required(login_url='login')
def Contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        try:
            # Save contact message to database
            contact_msg = Comments.objects.create(
                name=name,
                email=email,
                message=message
            )
            messages.success(request, 'Thank you! Your message has been sent successfully.')
            return render(request, './Contact.html')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
            return render(request, './Contact.html')
    
    return render(request, './Contact.html')

@login_required(login_url='login')
def About(request):
    return render(request, './About.html')

def Logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# Create your views here.
