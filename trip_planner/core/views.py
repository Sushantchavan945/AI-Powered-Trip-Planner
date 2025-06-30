from django.shortcuts import render,redirect
from .models import *
import google.generativeai as genai
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.db.models import Q
# Create your views here.

def index(request):
    return render(request,'home.html')


def plan_trip(request):
    if request.method=='POST':
        destination=request.POST.get('destination')
        request.session['destination']=destination
        return redirect('trip_time')
    return render(request,'plan_trip.html')


def trip_time(request):
    if request.method=='POST':
        start_date=request.POST.get('start_date')
        end_date=request.POST.get('end_date')
        request.session['start_date']=start_date
        request.session['end_date']=end_date

        return redirect('trip_type')
    return render(request,'trip_time.html')


def trip_type(request):
    if request.method=='POST':
        trip_type=request.POST.get('trip_type')
        request.session['trip_type']=trip_type
        return redirect('spending_type')
    return render(request,'trip_type.html')


def spending_type(request):
    if request.method == 'POST':
        selected_spending_ids = request.POST.getlist('spending_types')
        
        # Get session data and convert dates from strings to date objects
        destination = request.session.get('destination')
        start_date_str = request.session.get('start_date')
        end_date_str = request.session.get('end_date')
        trip_type = request.session.get('trip_type')

        # Convert string dates to date objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            messages.error(request, "Invalid date format. Please try again.")
            return redirect('plan_trip')

        # Create the Trip object with date objects
        trip = Trip.objects.create(
            
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            trip_type=trip_type,
        )

        # Set ManyToMany field
        trip.spending_types.set(selected_spending_ids)
        
        # Clear session
        request.session.flush()
        
        # Start generating the plan in the background
        from threading import Thread
        Thread(target=generate_and_save_trip_plan, args=(trip.id,)).start()
        
        return redirect('trip_detail', trip_id=trip.id)
    
    spending_types = Spending_Type.objects.all()
    return render(request, 'spending_time.html', {
        'spending_types': spending_types,
    })

def generate_and_save_trip_plan(trip_id):
    """Background task to generate and save trip plan"""
    trip = Trip.objects.get(id=trip_id)
    generated_plan = generate_trip_plan(trip)
    
    if generated_plan:
        trip.plan = {
            'generated_at': datetime.now().isoformat(),
            'content': generated_plan
        }
        trip.save()


GEMINI_API_KEY = "AIzaSyD-0xVHVa-NwFksKKybtro2QQlDDE0KCPs"
genai.configure(api_key=GEMINI_API_KEY)
def generate_trip_plan(trip):
    """Generate trip plan using Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        
        # Prepare prompt with trip details
        spending_types = ", ".join([st.get_name_display() for st in trip.spending_types.all()])
        duration = (trip.end_date - trip.start_date).days + 1
        
        prompt = f"""
    You are an expert travel consultant creating a concise, personalized trip itinerary. Keep the response focused and practical - aim for 2-3 pages of quality content.
    
    **Trip Details:**
    - Destination: {trip.destination}
    - Trip Type: {trip.trip_type.title()}
    - Duration: {duration} days ({trip.start_date.strftime('%B %d')} to {trip.end_date.strftime('%B %d, %Y')})
    - Traveler Interests: {spending_types}
    
    **Create a focused itinerary with these sections:**
    
    ## 🌟 Destination Highlights
    - 2-3 sentences on why {trip.destination} is perfect for {trip.trip_type.lower()} travelers
    - Key attractions that match their interests in: {spending_types}
    
    ## 📅 Daily Itinerary
    For each day, provide ONE key activity per time slot:
    - **Morning**: Main attraction/activity (include name, 2-hour duration)
    - **Afternoon**: Secondary activity or exploration
    - **Evening**: Dining recommendation with specific restaurant name
    
    Keep each day description to 3-4 bullet points maximum.
    
    ## 🍽️ Must-Try Food
    - 3-4 signature local dishes
    - 1-2 restaurant recommendations per budget level (budget/mid-range/upscale)
    
    ## 🚗 Getting Around
    - Best transportation method (2-3 sentences)
    - Key logistics tip
    
    ## 💡 Essential Tips
    - Best time to visit main attractions
    - One money-saving tip
    - One cultural etiquette tip
    - Packing essential specific to this trip
    
    **Formatting Requirements:**
    - Use ## for main sections, ### for days (Day 1, Day 2, etc.)
    - Bold restaurant names and attraction names
    - Keep bullet points concise (1-2 lines each)
    - Include emojis for visual appeal
    - Focus on quality over quantity
    
    **Content Guidelines:**
    - Maximum 2-3 pages when printed
    - Prioritize the most important/unique experiences
    - Be specific with names and locations
    - Keep descriptions concise but engaging
    - Focus on practical, actionable information
    
    Create a trip plan that's comprehensive yet concise - quality over quantity!
    """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating trip plan: {str(e)}")
        return "We couldn't generate the trip plan at this time. Please try again later."


def trip_detail(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    return render(request, 'trip_detail.html', {'trip': trip})


def my_trips(request):
    
    trips = Trip.objects.all().order_by('-start_date')
        
        # Debug output (remove in production)
    print(f"User {request.user.id} has {trips.count()} trips")
        
    return render(request, 'my_trips.html', {
            'trips': trips
            # Pass for additional verification
        })

