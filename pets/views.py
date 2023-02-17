from django.shortcuts import render,redirect
from django.contrib import messages

from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout

from .forms import UserAddForm,AddPetForm,AddBookingForm,AddVaccineForm
from .models import PetProfile,Booking,Vaccination
from doctors.models import DoctorProfile

from .decorators import pet_only, not_auth_pet
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
 
 
# authorize razorpay client with API Keys.
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

# Create your views here.


def index(request):
    return render(request, "home.html")

@pet_only
def pet_home(request):
    return render(request, "pets/pet-home.html")

@not_auth_pet
def signup(request):  # first get the user form from forms.py to render with signup.html
    signup_form = UserAddForm()
    if(request.method == "POST"):
        form = UserAddForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            username = form.cleaned_data.get("password")
            if User.objects.filter(username=username).exists():
                messages.info(request, "Username Already Taken !!! Retry")
                return redirect("signup")
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Already Taken !!! Retry")
                return redirect("signup")
            else:
                new_user = form.save()
                new_user.save()

                # getting and assigning group to the user
                group = Group.objects.get(name="pets")
                new_user.groups.add(group)
                messages.info(request, "Pet Account Created")
                return redirect("signin")
        else:
            messages.info(
                request, "Fom validation Failed!!! Try a defferent password.")

    return render(request, "pets/signup.html", {"signup_form": signup_form})


@not_auth_pet
def signin(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            request.session["username"] = username
            request.session["password"] = password
            login(request, user)
            return redirect("pet_home")
        else:
            messages.info(request, "Username or password incorrect ")
            return redirect("signin")
    return render(request, "pets/signin.html")

@pet_only
def signout(request):
    logout(request)
    return redirect("signin")

@pet_only
def add_user_profile(request):
    form = AddPetForm()
    if request.method == "POST":
        add_form = AddPetForm(request.POST,request.FILES)
        if(add_form.is_valid()):
            user = User.objects.get(id=request.user.id)
            updated_profile = add_form.save()
            updated_profile.user_ID = user
            updated_profile.save()
            return redirect("pet_home")
    return render(request, "pets/add-profile.html",{"form":form})

@pet_only
def view_user_profile(request):
    pet = PetProfile.objects.filter(user_ID=request.user.id)
    if(len(pet) == 0):
        return redirect("add_user_profile")
    return render(request,"pets/pet-profile.html",{"pet":pet[0]})

@pet_only
def view_all_doctors(request):
    all_doctors = DoctorProfile.objects.all()
    return render(request,"pets/view-all-doctors.html",{"all_doctors":all_doctors})

@pet_only
def view_doctor_profile(request,id):
    doctor = DoctorProfile.objects.get(id=id)
    return render(request,"pets/doctor-profile.html",{"doctor":doctor})

@pet_only
def book_doctor(request,id):
    doctor = DoctorProfile.objects.get(id=id)
    form = AddBookingForm()
    if request.method == "POST":
        add_form = AddBookingForm(request.POST,request.FILES)
        if(add_form.is_valid()):
            booked_form = add_form.save()
            patient = User.objects.get(id=request.user.id)
            booked_form.Patient_ID = patient.id
            booked_form.Patient_Name = patient.username
            booked_form.Doctor_ID = doctor.doctor_ID
            booked_form.Doctor_Name = doctor.Doctor_name
            booked_form.status = "Payment Pending"
            booked_form.save()
            return redirect("payment_page")
    return render(request,"pets/book-doctor.html",{"doctor":doctor,"form":form})


@pet_only
def view_my_bookings(request):
    all_bookings = Booking.objects.filter(Patient_ID=request.user.id,status="Booked")
    return render(request,"pets/view-all-bookings.html",{"all_bookings":all_bookings})

def user_cancel_booking(request,id):
    booking = Booking.objects.get(id=id)
    booking.status = "Cancelled"
    booking.save()
    return redirect("view_my_bookings")

@pet_only
def add_vaccine(request):
    form = AddVaccineForm()
    if request.method == "POST":
        add_form = AddVaccineForm(request.POST,request.FILES)
        print(request.FILES)
        if(add_form.is_valid()):
            vaccine_form = add_form.save()
            pet = PetProfile.objects.get(user_ID=request.user.id)
            vaccine_form.user_ID = request.user
            vaccine_form.Pet_name = pet.Pet_name
            vaccine_form.save()
            return redirect("view_my_vaccines")
    return render(request, "pets/add-vaccine.html",{"form":form})


@pet_only
def view_my_vaccines(request):
    all_vaccines = Vaccination.objects.filter(user_ID=request.user.id)
    return render(request,"pets/view-all-vaccines.html",{"all_vaccines":all_vaccines})

@pet_only
def payment_page(request):
    currency = 'INR'
    amount = 50000  # Rs. 200
    # Create a Razorpay Order
    razorpay_order = razorpay_client.order.create(dict(amount=amount,currency=currency, payment_capture='0'))

    # order id of newly created order.
    razorpay_order_id = razorpay_order['id']
    callback_url = 'http://127.0.0.1:8001/paymenthandler/'
 
    # we need to pass these details to frontend.
    context = {}
    context['razorpay_order_id'] = razorpay_order_id
    context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
    context['razorpay_amount'] = amount
    context['currency'] = currency
    context['callback_url'] = callback_url
    print(context)
    return render(request, 'pets/payment-page.html', context=context)

# we need to csrf_exempt this url as
# POST request will be made by Razorpay
# and it won't have the csrf token.
@csrf_exempt
def paymenthandler(request):
    # only accept POST request.
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')
            params_dict = {'razorpay_order_id': razorpay_order_id,'razorpay_payment_id': payment_id,'razorpay_signature': signature}
 
            # verify the payment signature.
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            print("result : ",result)
            if result is not None:
                amount = 50000  # Rs. 200
                try:
                    # capture the payemt
                    razorpay_client.payment.capture(payment_id, amount)
                    booking = Booking.objects.all().last()
                    booking.status = "Booked"
                    booking.save()
                    # render success page on successful caputre of payment
                    return redirect("view_my_bookings")

                except:
                    # if there is an error while capturing payment.
                    return redirect("view_my_bookings")

            else:
                # if signature verification fails.
                return redirect("view_my_bookings")
        except:
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
       # if other than POST request is made.
        return HttpResponseBadRequest()