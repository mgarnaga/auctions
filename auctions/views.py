from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from . import util

from .models import User, Category, Listing, Bid, Comment, Watchlist

class NewListingForm(forms.Form):
    title = forms.CharField(label='Title')
    description = forms.CharField(label='', widget=forms.Textarea(attrs={
        "class": "listing_form", "placeholder":"Enter your item descriprion here"}))
    price = forms.DecimalField(label='Starting Bid, $', max_digits=7, decimal_places=2)
    image = forms.URLField(label='Link to product image (optional)', required=False)
    category = forms.ChoiceField(label='Category (optional)', choices=Category.choices, required=False)

class NewCommentForm(forms.Form):
    comment = forms.CharField(label='', widget=forms.Textarea(attrs={"class": "comment_form"}))

class NewBidForm(forms.Form):
    bid = forms.DecimalField(label='Your bid', max_digits=9, decimal_places=2, min_value=0.01)


def index(request):
    # filtering active listings and calculating current price via helper function
    listing_objects = Listing.objects.filter(active=True)
    active_listings = listing_objects.all()
    active_list = []
    for item in active_listings:
        best_bidding = util.best_bid(item)[0]
        active_list += [(item, best_bidding)]
    return render(request, "auctions/index.html", {
        "active_listings":active_list
    })

@login_required(login_url='/login')
def listing(request, listing_id):

    # getting the listings and bids for the listing. calculating best bid and current winner via hepler function
    listing = Listing.objects.get(pk=listing_id)
    winning_bid, current_winner = util.best_bid(listing)
    bid_objects = Bid.objects.filter(product=listing)
    all_bids = bid_objects.all()

    # getting all comments for the listing
    comment_objects = Comment.objects.filter(related_to=listing)
    all_comments = comment_objects.all()

    # checking if listing is in users watchlist, if not setting to false
    if request.user.is_authenticated:
        try:
            favorite = Watchlist.objects.get(fave=listing, user=request.user)
        except (KeyError, Watchlist.DoesNotExist):
            favorite = Watchlist.objects.create(user=request.user, fave=listing)
            favorite.save()
            
    # if bid was placed
    if request.method == "POST":
        if request.POST['action'] == "Go!":
            # getting the bid data
            bid_form = NewBidForm(request.POST)
            if bid_form.is_valid():
                bid = bid_form.cleaned_data["bid"]

                # if it's the first bid and it's equal or greater than initial price, or it's greater than current best bid,
                # then creating new bid and redirecting to listing page
                if not all_bids and bid >= listing.price or bid > winning_bid:
                    new_bid = Bid.objects.create(user=request.user, product=listing, the_bid=bid)
                    new_bid.save()
                    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
                else:
                    return render(request, "auctions/listing.html", {
                        "listing":listing,
                        "bid_form":bid_form,
                        "bid_log":all_bids,
                        "current_win":winning_bid,
                        "current_winner":current_winner,
                        "favorited":favorite.added,
                        "comment_form":NewCommentForm(),
                        "comment_log":all_comments,
                        "message": "Your bid must be greater than the current winning bid/initial price."
                    })
                
        # if comment form is received
        if request.POST['action'] == "Add Comment":
            comment_form = NewCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.cleaned_data["comment"]
                new_comment = Comment.objects.create(text=comment, related_to=listing, author=request.user)
                new_comment.save()
                return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
            else:
                return render(request, "auctions/listing.html", {
                        "listing":listing,
                        "bid_form":bid_form,
                        "bid_log":all_bids,
                        "current_win":winning_bid,
                        "current_winner":current_winner,
                        "favorited":favorite.added,
                        "comment_form":comment_form,
                        "comment_log":all_comments,
                        "message": "Make sure you filled out the comment form."
                    })
        
        # adding to watchlist
        if request.POST['action'] == "Add to Watchlist":
            favorite.added = True
            favorite.save()
        
        # removing from watchlist
        if request.POST['action'] == "Remove from Watchlist":
            favorite.added = False
            favorite.save()

        # closing auction
        if request.POST['action'] == "Close auction":
            listing.active = False
            listing.save()


    # default GET render
    return render(request, "auctions/listing.html", {
        "listing":listing,
        "bid_form":NewBidForm(),
        "bid_log":all_bids,
        "current_win":winning_bid,
        "current_winner":current_winner,
        "favorited":favorite.added,
        "comment_form":NewCommentForm(),
        "comment_log":all_comments
    })

@login_required(login_url='/login')
def create(request):
    if request.method == "POST":
        # getting form contents, checking its valid and saving as a new listing 
        listing_form = NewListingForm(request.POST)
        if listing_form.is_valid():
            title = listing_form.cleaned_data["title"]
            category = listing_form.cleaned_data["category"]
            description = listing_form.cleaned_data["description"]
            price = listing_form.cleaned_data["price"]
            pic = listing_form.cleaned_data["image"]
            try:
                new_listing = Listing.objects.create(
                    title=title, category=category, description=description, price=price, pic=pic, active=True, owner=request.user)
                new_listing.save()
                return HttpResponseRedirect(reverse("listing", args=(new_listing.id,)))
            except IntegrityError:
                return render(request, "auctions/create.html", {
                    "message": "Something went wrong. Please check that you filled out the form below.",
                    "listing_form":listing_form
                })
        else:
            return render(request, "auctions/create.html", {
                    "message": "Please check that you correctly filled out the form below.",
                    "listing_form":listing_form
                })
    
    # GET render
    return render(request, "auctions/create.html", {
        "message": None,
        "listing_form": NewListingForm()
    })


@login_required(login_url='/login')
def watchlist(request):

    # filtering users watchlist items and setting listings list that goes to template
    fav_objects = Watchlist.objects.filter(user=request.user, added=True)
    favorites = fav_objects.all()
    favlist = []

    # iterating over favorites to get listings and add them to list
    for object in favorites:
        try:
            favorite = Listing.objects.get(pk=object.fave.id)
            price = util.best_bid(favorite)[0]
            favlist += [(favorite, price)]
        except (KeyError, Listing.DoesNotExist):
            favorite = None
            price = None

    # if user deletes closed listing from watchlist
    if request.method == "POST":
        id = request.POST["id"]
        item = Listing.objects.get(pk=id)
        watchlisted = Watchlist.objects.get(fave=item, user=request.user)
        watchlisted.added = False
        watchlisted.save()
        return HttpResponseRedirect(reverse("watchlist"))

    return render(request, "auctions/watchlist.html", {
        "favorites":favlist
    })


def categories(request):
    return render(request, "auctions/categories.html", {
        # slice excludes 0 which is None category
        "categories":Category.choices[1:]
    })

# getting listings that are the required category and it's current price
def category(request, name):
    relevant_list = []
    category_objects = Listing.objects.filter(category=name, active=True)
    category_listings = category_objects.all()
    for cat_listing in category_listings:
        price = util.best_bid(cat_listing)[0]
        relevant_list += [(cat_listing, price)]

    return render(request, "auctions/category.html", {
        "name":name,
        "listings":relevant_list
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
