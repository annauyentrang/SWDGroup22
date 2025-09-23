from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def match_volunteer(request, volunteer_id):
    volunteer = {"id": volunteer_id, "name": f"Volunteer {volunteer_id}"}
    events = [
        {"id": 1, "title": "Food Drive"},
        {"id": 2, "title": "Park Cleanup"},
        {"id": 3, "title": "Blood Donation"},
    ]
    chosen = None
    if request.method == "POST":
        selected_id = request.POST.get("event")
        chosen = next((e for e in events if str(e["id"]) == selected_id), None)
    return render(request, "match_form.html", {
        "volunteer": volunteer, "events": events, "chosen": chosen
    })