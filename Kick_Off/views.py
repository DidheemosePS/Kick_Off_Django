import json
import mimetypes
from urllib.parse import urlparse
from django.http import HttpResponse, JsonResponse
from .s3 import delete_file, upload_file
from .models import Event, Cart, Ticket
from django.shortcuts import render, redirect
from django.shortcuts import redirect, render
from . forms import SignupForm, LoginForm, CreateEventsForm
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Sum
from django.utils.timezone import now
from django.conf import settings
from django_email.email_utils import send_html_email
import random

def index(request):
    # event_date___gte used to find the events available in future, To avoid the expried events and __gte means '>='
    today = now().date()
    events = Event.objects.filter(event_date__gte=today).annotate(
        booked_tickets=Sum('ticket_events__event_number_of_tickets')).values(
        'id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'booked_tickets', 'event_image_url', 'event_video_url').order_by('-updated')
    # generate random events from queryset to display in the carousel
    random_events = random.sample(list(events), min(5, len(events)))
    return render(request, 'index.html', {'title': 'Kick Off', 'page_url': "book_now", 'events': events, 'random_events': random_events})


def search(request):
    # event_date___gte used to find the events available in future, To avoid the expried events and __gte means '>='
    today = now().date()
    search_value = request.GET.get('search_query')
    # Q is used to perform OR logical operation
    search_result = Event.objects.filter(Q(event_date__gte=today) & Q(event_name__icontains=search_value) | Q(event_venue_name__icontains=search_value) | Q(organisation_name__icontains=search_value)).annotate(
        booked_tickets=Sum('ticket_events__event_number_of_tickets')).values(
        'id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'booked_tickets').order_by('-updated')
    events = Event.objects.filter(event_date__gte=today).values(
        'id', 'event_image_url').order_by('-updated')
    # generate random events from queryset to display in the carousel
    random_events = random.sample(list(events), min(5, len(events)))
    return render(request, 'index.html', {'title': 'Search - Kick Off', 'page_url': "book_now", 'events': search_result, 'random_events': random_events})


@login_required(login_url="login")
def book_now(request, id):
    # event_date___gte used to find the events available in future, To avoid the expried events and __gte means '>='
    today = now().date()
    event_details = Event.objects.filter(event_date__gte=today, id=id)
    if not event_details:
        return HttpResponse("This event is not available")
    book_mark = Cart.objects.filter(
        participant=request.user, event=Event.objects.get(pk=id))
    if not book_mark:
        return render(request, 'book_now.html', {'title': 'Book Now - Kick Off', 'event_details': event_details[0], 'book_mark': False})
    return render(request, 'book_now.html', {'title': 'Book Now - Kick Off', 'event_details': event_details[0], 'book_mark': True})


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['account_type'] == 'Participant':
                user.is_participant = True
            if form.cleaned_data['account_type'] == 'Organisation':
                user.is_organisation = True
            user.save()
            username = form.cleaned_data['username']
            receiver = form.cleaned_data['email']
            context = {
                'name': username,
                'subject': 'Account Signup Confirmation',
                'body': ["Welcome to Kick Off! We're thrilled to have you join us.", "Your account has been successfully created.", "If you have any questions or need assistance, feel free to contact our support team.", "Thank you and enjoy your experience!"],
                'company': 'Kick Off',
                'from_email': settings.EMAIL_HOST_USER,
                'to': [receiver],
                'reply_to': [settings.EMAIL_HOST_USER]
            }
            send_html_email('email_welcome', context)
            return redirect('login')
        return render(request, 'signup.html', {'signup_form': form})
    form = SignupForm()
    return render(request, 'signup.html', {'title': 'Signup - Kick Off', 'signup_form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                auth.login(request, user)
                context = {
                    'name': user,
                    'company': 'Kick Off',
                    'subject': 'Login Confirmation',
                    'from_email': settings.EMAIL_HOST_USER,
                    'to': [request.user.email],
                    'reply_to': [settings.EMAIL_HOST_USER]
                }
                send_html_email('email_login', context)
                next_url = request.GET.get('next', '')
                return redirect(next_url)
        return render(request, 'login.html', {'login_form': form})
    form = LoginForm()
    return render(request, 'login.html', {'title': 'Login - Kick Off', 'login_form': form})


def logout(request):
    auth.logout(request)
    return redirect('')


@login_required(login_url="login")
def create_events(request):
    if not request.user.is_organisation:
        return redirect('login')
    if request.method == 'POST':
        form = CreateEventsForm(request.POST, request.FILES)
        if form.is_valid():
            event_image = request.FILES['event_image']
            image_key = f"kick_off/images/{event_image}"
            image_content_type = mimetypes.guess_type(event_image.name)[0]
            event_video = request.FILES['event_video']
            video_key = f"kick_off/videos/{event_video}"
            video_content_type = mimetypes.guess_type(event_video.name)[0]
            event_image_response = upload_file(
                event_image, 'x23176245-s3-bucket', image_key, image_content_type)
            event_video_response = upload_file(
                event_video, 'x23176245-s3-bucket', video_key, video_content_type)
            create_event = form.save(commit=False)
            create_event.organisation_name = request.user
            create_event.organisation = request.user
            if event_image_response is not False and event_video_response is not False:
                create_event.event_image_url = event_image_response
                create_event.event_video_url = event_video_response
            else:
                create_event.event_image_url = ''
                create_event.event_video_url = ''
            create_event.save()
            return redirect('view_scheduled_events')
    form = CreateEventsForm()
    return render(request, 'create_events.html', {'title': 'Create Event - Kick Off', 'create_events_form': form, 'submit_button_value': "Create"})


@login_required(login_url="login")
def view_scheduled_events(request):
    if not request.user.is_organisation:
        return redirect('login')
    today = now().date()
    view_scheduled_events = Event.objects.filter(organisation=request.user).annotate(booked_tickets=Sum(
        'ticket_events__event_number_of_tickets')).values('id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'booked_tickets', 'event_image_url', 'event_video_url').order_by('-updated')
    events = Event.objects.filter(event_date__gte=today).values(
        'id', 'event_image_url').order_by('-updated')
    # generate random events from queryset to display in the carousel
    random_events = random.sample(list(events), min(5, len(events)))
    return render(request, 'index.html', {'title': 'Scheduled Events - Kick Off', 'page_url': "view_scheduled_event_details", 'events': view_scheduled_events, 'random_events': random_events})


@login_required(login_url="login")
def view_scheduled_event_details(request, id):
    if not request.user.is_organisation:
        return redirect('login')
    view_scheduled_event_details = Event.objects.filter(
        organisation=request.user, id=id)[0]
    return render(request, 'book_now.html', {'title': 'Scheduled Event Details - Kick Off', 'organisation_id': request.user.id, 'event_details': view_scheduled_event_details})


@login_required(login_url="login")
def save_this_event(request):
    if not request.user.is_participant:
        return JsonResponse({'login_required': True})
    if request.method == 'POST':
        # json.loads(request.POST) used to get the data from the POST request, request.POST can be used only in the form submissions
        id = json.loads(request.body)['id']
        # event = Event.objects.get(pk=id) to create Event model instance
        if not Cart.objects.filter(participant=request.user, event=Event.objects.get(pk=id)):
            Cart.objects.create(
                participant=request.user, event=Event.objects.get(pk=id))
            return JsonResponse({'bookmarked': True})
        else:
            Cart.objects.filter(
                participant=request.user, event=Event.objects.get(pk=id)).delete()
            return JsonResponse({'bookmarked': False})
    return JsonResponse({'status': 'Invalid request'})


@login_required(login_url="login")
def saved_events(request):
    if not request.user.is_participant:
        return redirect('login')
    today = now().date()
    fetch_saved_events = Event.objects.filter(
        cart_events__participant=request.user).values(
        'id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'event_image_url', 'event_video_url').order_by('-updated')
    if not fetch_saved_events:
        return HttpResponse('No saved events')
    events = Event.objects.filter(event_date__gte=today).values(
        'id', 'event_image_url').order_by('-updated')
    # generate random events from queryset to display in the carousel
    random_events = random.sample(list(events), min(5, len(events)))
    return render(request, 'index.html', {'title': 'Saved Events - Kick Off', 'page_url': "book_now", 'events': fetch_saved_events, 'random_events': random_events})


@login_required(login_url="login")
def book_tickets(request, id):
    if not request.user.is_participant:
        return redirect('login')
    # event_date___gte used to find the events available in future, To avoid the expried events and __gte means '>='
    today = now().date()
    ticket_details = Event.objects.filter(event_date__gte=today, id=id).values(
        'id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'event_number_of_tickets', 'event_ticket_price')
    if not ticket_details:
        return HttpResponse("This event is not available")
    ticket_count = ticket_details[0]['event_number_of_tickets']
    if ticket_count == 0:
        return HttpResponse("No tickets left")
    return render(request, 'book_tickets.html', {'title': 'Book Tickets - Kick Off', 'ticket_details': ticket_details[0]})


@login_required(login_url="login")
def view_scheduled_event_details_delete(request, id):
    if not request.user.is_organisation:
        return redirect('login')
    event_delete= Event.objects.filter(organisation=request.user, id=id)[0]
    image_key = urlparse(event_delete.event_image_url).path.lstrip('/')
    video_key = urlparse(event_delete.event_video_url).path.lstrip('/')
    if image_key and video_key is not None:
        delete_file('x23176245-s3-bucket', image_key)
        delete_file('x23176245-s3-bucket', video_key)
    event_delete.delete()
    return redirect('view_scheduled_events')


@login_required(login_url="login")
def view_scheduled_event_details_edit(request, id):
    if not request.user.is_organisation:
        return redirect('login')
    event_edit = Event.objects.filter(organisation=request.user, id=id)[0]
    if request.method == 'POST':
        form = CreateEventsForm(
            request.POST, request.FILES, instance=event_edit)
        if form.is_valid():
            if 'event_image' in form.changed_data and form.cleaned_data['event_image']:
                image_key = urlparse(
                    event_edit.event_image_url).path.lstrip('/')
                if image_key is not None:
                    delete_file('x23176245-s3-bucket', image_key)
                event_image = request.FILES['event_image']
                image_key = f"kick_off/images/{event_image}"
                content_type = mimetypes.guess_type(event_image.name)[0]
                event_image_response = upload_file(
                    event_image, 'x23176245-s3-bucket', image_key, content_type)
                if event_image_response is not False:
                    event_edit.event_image_url = event_image_response
            if 'event_video' in form.changed_data and form.cleaned_data['event_video']:
                video_key = urlparse(
                    event_edit.event_video_url).path.lstrip('/')
                if video_key is not None:
                    delete_file('x23176245-s3-bucket', video_key)
                event_video = request.FILES['event_video']
                video_key = f"kick_off/videos/{event_video}"
                content_type = mimetypes.guess_type(event_video.name)[0]
                event_video_response = upload_file(
                    event_video, 'x23176245-s3-bucket', video_key, content_type)
                if event_video_response is not False:
                    event_edit.event_video_url = event_video_response
            form.save()
            return redirect('view_scheduled_events')
    form = CreateEventsForm(instance=event_edit)
    return render(request, 'create_events.html', {'title': 'Scheduled Event Edit - Kick Off', 'create_events_form': form, 'event_edit': event_edit, 'submit_button_value': "Update"})


@login_required(login_url="login")
def make_payment(request, id):
    if not request.user.is_participant:
        return JsonResponse({'login_required': True})
    if request.method == 'POST':
        # json.loads(request.POST) used to get the data from the POST request, request.POST can be used only in the form submissions
        Ticket.objects.create(
            event=Event.objects.get(pk=id), participant=request.user, event_number_of_tickets=json.loads(request.body)['event_number_of_tickets'], event_ticket_price=json.loads(request.body)['event_ticket_price'])
        Event.objects.filter(id=id).update(event_number_of_tickets=F(
            'event_number_of_tickets')-json.loads(request.body)['event_number_of_tickets'])
        event = Event.objects.get(pk=id)
        context = {
            'event': event.event_name,
            'venue': event.event_venue_name,
            'date': event.event_date,
            'time': event.event_time,
            'tickets': json.loads(request.body)['event_number_of_tickets'],
            'company': 'Kick Off',
            'subject': 'Event Ticket Booking Confirmation',
            'from_email': settings.EMAIL_HOST_USER,
            'to': [request.user.email],
            'reply_to': [settings.EMAIL_HOST_USER]
        }
        send_html_email('email_ticket', context)
        return JsonResponse({'payment_status': True})
    return JsonResponse({'status': 'Invalid request'})


@login_required(login_url="login")
def tickets_booked(request):
    if not request.user.is_participant:
        return redirect('login')
    fetch_tickets_booked = Event.objects.filter(ticket_events__participant=request.user).annotate(
        number_of_tickets=F('ticket_events__event_number_of_tickets'),
        ticket_price=F('ticket_events__event_ticket_price'),
        ticket_created=F('ticket_events__created')).order_by('-ticket_events__created').values(
        'id', 'event_name', 'event_venue_name', 'event_date', 'event_time', 'number_of_tickets', 'ticket_price', 'ticket_created')
    if not fetch_tickets_booked:
        return HttpResponse('No tickets booked yet')
    return render(request, 'tickets_booked.html', {
        'title': 'Tickets Booked - Kick Off', 'ticket_details': fetch_tickets_booked, 'text': "Amount Paid"
    })
