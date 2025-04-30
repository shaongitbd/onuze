import math
from datetime import datetime, timedelta

def calculate_hotness(ups, downs, created_at):
    """
    Calculate the 'hotness' score of a post based on votes and time
    Similar to the original Reddit 'hot' algorithm
    
    Args:
        ups (int): Upvote count
        downs (int): Downvote count
        created_at (datetime): When the post was created
        
    Returns:
        float: A score indicating the post's 'hotness'
    """
    score = ups - downs
    order = math.log10(max(abs(score), 1))
    sign = 1 if score > 0 else -1 if score < 0 else 0
    
    # Get seconds since epoch for the creation time
    epoch = datetime(1970, 1, 1)
    seconds = (created_at - epoch).total_seconds() - 1643000000  # Arbitrary offset
    
    return round(sign * order + seconds / 45000, 7)


def calculate_trending(ups, downs, view_count, comment_count, created_at):
    """
    Calculate the 'trending' score of a post based on activity and time
    Prioritizes recent posts with high engagement rates
    
    Args:
        ups (int): Upvote count
        downs (int): Downvote count
        view_count (int): Number of views
        comment_count (int): Number of comments
        created_at (datetime): When the post was created
        
    Returns:
        float: A score indicating how 'trending' the post is
    """
    # Calculate time decay factor (newer posts get higher scores)
    now = datetime.now()
    post_age_hours = max((now - created_at).total_seconds() / 3600, 1)
    time_decay = 1 / (post_age_hours ** 0.8)
    
    # Calculate engagement rate
    total_votes = ups + downs
    if total_votes == 0:
        vote_ratio = 0
    else:
        vote_ratio = ups / total_votes
        
    # Weight different activities
    engagement = (
        vote_ratio * 10 + 
        (comment_count / max(post_age_hours, 1)) * 5 + 
        (view_count / max(post_age_hours, 1)) * 0.2
    )
    
    trending_score = engagement * time_decay
    return round(trending_score, 7)


def calculate_controversy(ups, downs):
    """
    Calculate the 'controversy' score of a post
    Posts with balanced up/downvotes will have higher controversy
    
    Args:
        ups (int): Upvote count
        downs (int): Downvote count
        
    Returns:
        float: A score indicating how controversial the post is
    """
    # If there are no votes or all votes are in one direction, not controversial
    if ups <= 0 or downs <= 0:
        return 0
        
    magnitude = ups + downs
    balance = float(min(ups, downs)) / max(ups, downs)
    
    # Higher when votes are balanced and there are many votes
    controversy = magnitude * balance * 4
    return round(controversy, 7) 