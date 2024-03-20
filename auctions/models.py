from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.TextChoices):
    NONE = ""
    CLOTHES = "Clothes"
    WEAPONS = "Weapons"
    OBJECTS = "Objects"
    EXTRAS = "Extras"


class Listing(models.Model):
    title = models.CharField(max_length=64)
    category = models.CharField(max_length=7, choices=Category.choices, blank=True)
    description = models.TextField() # textarea
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    pic = models.URLField(blank=True, null=True) # input type url
    active = models.BooleanField(default=True)
    date = models.DateField(auto_now=False, auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")

    def __str__(self):
        return f'{self.title}'
    

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users")
    product = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="products")
    the_bid = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f'Bid ${self.the_bid}, on {self.product} by {self.user}'


class Comment(models.Model):
    text = models.TextField()
    date = models.DateField(auto_now=False, auto_now_add=True)
    related_to = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="about_listing")
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="authors")

    def __str__(self):
        return f'Comment on {self.related_to} by {self.author}'


class Watchlist(models.Model):
    added = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fave = models.ForeignKey(Listing, on_delete=models.CASCADE)
    