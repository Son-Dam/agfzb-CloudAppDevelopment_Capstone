from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarDealer,CarModel
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)



def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)
# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request,**kwargs):
    context ={}
    st = kwargs.get("st")
    if request.method == "GET":
        url = "https://us-east.functions.appdomain.cloud/api/v1/web/Son%20Dam_djangoserver-space/dealership-package/get-dealership"
        # Get dealers from the URL
        if st:
            dealerships = get_dealers_from_cf(url,st = st)
        else:
            dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        context["dealerships"] = dealerships
        
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    context={}
    
    if request.method == "GET":
        url = "https://us-east.functions.appdomain.cloud/api/v1/web/Son%20Dam_djangoserver-space/dealership-package/get-review"
        
        reviews = get_dealer_reviews_from_cf(url, dealerId = dealer_id)
        context['dealer'] = get_dealers_from_cf("https://us-east.functions.appdomain.cloud/api/v1/web/Son%20Dam_djangoserver-space/dealership-package/get-dealership",
                                            dealerId = dealer_id)[0]
        context['reviews'] = reviews
       
        # Return a list of reviews
        return render(request, 'djangoapp/dealer_details.html', context)
# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    context = {}
    
    if request.method == "GET":
        context['dealer'] = get_dealers_from_cf("https://us-east.functions.appdomain.cloud/api/v1/web/Son%20Dam_djangoserver-space/dealership-package/get-dealership",
                                            dealerId = dealer_id)[0]
        cars = CarModel.objects.filter(dealerId=dealer_id)
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    if request.method == "POST":
        if request.user.is_authenticated:
            car = get_object_or_404(CarModel, pk=request.POST["car"])
            json_payload ={}        
            review = dict()
            review['name'] = request.user.username
            review["time"] =datetime.utcnow().isoformat()
            review["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    review["purchase"] = True
            review["purchase_date"] = request.POST["purchasedate"]
            review["car_make"] = car.carMake.name
            review["car_model"] = car.name
            review["car_year"] = int(car.year.strftime("%Y"))
            review["dealership"] = dealer_id
            review["review"] = request.POST['content']
            json_payload['review'] = review
            response = post_request("https://us-east.functions.appdomain.cloud/api/v1/web/Son%20Dam_djangoserver-space/dealership-package/post-review",
                                    json_payload = json_payload)
            
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
