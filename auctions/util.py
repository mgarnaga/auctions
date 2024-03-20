from .models import Bid

def best_bid(listing):
    bid_objects = Bid.objects.filter(product=listing)
    all_bids = bid_objects.all()
    if not all_bids:
        winning_bid = listing.price
        current_winner = None
    else:
        winning_bid = 0.0
        for bid in all_bids:
            if bid.the_bid > winning_bid:
                winning_bid = bid.the_bid
                current_winner = bid.user
    return winning_bid, current_winner