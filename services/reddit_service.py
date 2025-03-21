import praw
import random
import os

class RedditService:
    """Service for fetching horror stories from Reddit"""
    
    def __init__(self, client_id, client_secret, user_agent):
        """Initialize the Reddit API client"""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Horror subreddits
        self.horror_subreddits = [
            "nosleep", 
            "shortscarystories", 
            "creepypasta", 
            "LetsNotMeet",
            "DarkTales",
            "TheCrypticCompendium",
            "libraryofshadows",
            "scarystories",
            "TrueScaryStories",
            "HorrorStories"
        ]
        
        # Cache file for used story IDs
        self.cache_file = "data/used_story_ids.txt"
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
    def get_subreddit_list(self):
        """Return the list of available horror subreddits"""
        return self.horror_subreddits
    
    def fetch_stories(self, subreddits=None, time_filter="week", limit=30, min_length=1000):
        """Fetch stories from selected subreddits"""
        if subreddits is None:
            # Randomly select 2-3 subreddits if none specified
            subreddits = random.sample(self.horror_subreddits, min(3, len(self.horror_subreddits)))
        
        # Fetch stories from selected subreddits
        all_posts = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = list(subreddit.top(time_filter, limit=limit))
                all_posts.extend(posts)
            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {str(e)}")
        
        # Shuffle posts to randomize selection
        random.shuffle(all_posts)
        
        # Filter out very short posts and previously used posts
        used_ids = set()
        
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                used_ids = set(line.strip() for line in f.readlines())
        
        filtered_posts = [
            post for post in all_posts 
            if post.id not in used_ids 
            and len(post.selftext) > min_length
        ]
        
        if not filtered_posts:
            filtered_posts = [post for post in all_posts if len(post.selftext) > min_length]
        
        return filtered_posts
    
    def mark_story_used(self, story_id):
        """Mark a story as used to avoid reuse"""
        with open(self.cache_file, 'a') as f:
            f.write(f"{story_id}\n") 