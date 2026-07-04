from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
from textblob import TextBlob
import tweepy
import praw
import requests
import random
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import io
import json

# ===========================
# CONFIGURATION & MOCK SETUP
# ===========================

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# NOTE: In a production environment, all keys should be stored in environment variables (e.g., using python-dotenv).
# We keep them here for runnability in the single-file context.

# API Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HF_SUMMARIZATION_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_HEADERS = {"Authorization": "Bearer hf_2Ix4zte9YnXFYK6A97FwB6LY8 "}
#TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAwZ4wEAAAAA7ofRxe7XrEDfZ889q20dNAIi0x4%3DpE2toyN1xZkcztPGNfpuuLFMIDAlF304BMps0awsQYo8cAsSwz"

# Twitter/Reddit API tokens (placeholders)
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAMIL4wEAAAAAlwvx7F1hs2xB5uF48BHl0s13HuA%3Dgny9QRZAbQv0nNvcOzpRTuqo4wAfVMV4PUJrfTNOVUpJRyaBEo"
REDDIT_CLIENT_ID = "Kl4mT25fYnGCVBZkY5ob5A"
REDDIT_CLIENT_SECRET = "LhkJsDKHq3LmqhXTU-TYObRSyx5vlQ"
REDDIT_USER_AGENT = "SentimentTracker/1.0"

@dataclass
class Post:
    """Structured data class for a single social media mention."""
    post_id: str
    text: str
    platform: str
    brand: str
    timestamp: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    sentiment: str = 'Neutral'
    polarity: float = 0.0
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    emotions: Dict[str, int] = field(default_factory=dict)
    location: str = 'Unknown'
    language: str = 'en'
    user_segment: str = 'General'

class MockDatabase:
    """
    Simulates a persistent database (e.g., MongoDB/PostgreSQL) for storing
    all collected social media posts and tracking active streams.
    """
    def __init__(self):
        # Stores all collected historical posts keyed by brand name
        self.posts_by_brand: Dict[str, List[Post]] = defaultdict(list)
        # Stores active streams for real-time monitoring
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        # Stores alert thresholds
        self.alert_thresholds: Dict[str, Dict[str, Any]] = {}

    def insert_post(self, post: Post):
        """Inserts a post into the database."""
        self.posts_by_brand[post.brand].append(post)

    def get_posts(self, brand: str, time_period: str = '7d') -> List[Post]:
        """Simulates querying historical data for a brand."""
        # For simulation, this will trigger sample data generation if not found
        if not self.posts_by_brand[brand]:
            # Simulate a "deep dive" historical fetch for this brand
            self.posts_by_brand[brand] = self._generate_varied_data(brand, time_period)
        
        # Filter posts by time period for realism (though data is static)
        cutoff = self._get_cutoff_date(time_period)
        return [p for p in self.posts_by_brand[brand] if datetime.fromisoformat(p.timestamp) >= cutoff]

    def _generate_varied_data(self, brand: str, time_period: str) -> List[Post]:
        """Generates realistic, but varied, sample data for comparison."""
        base_posts = generate_sample_data(num_posts=150)
        posts: List[Post] = []
        
        # Assign brand-specific sentiment profile
        profile = self._get_brand_profile(brand)
        
        for i, post in enumerate(base_posts):
            # Introduce brand-specific bias
            if random.random() < profile['sentiment_bias']:
                post_text = random.choice(profile['keywords'])
                sentiment, polarity = analyze_sentiment_textblob(post_text)
                
                # Force sentiment to align with profile for a subset of posts
                if random.random() < 0.3: # 30% chance to overwrite sentiment
                    sentiment = random.choices(['Positive', 'Negative'], weights=[profile['positive_skew'], 1 - profile['positive_skew']])[0]
                    polarity = random.uniform(0.5, 0.9) if sentiment == 'Positive' else random.uniform(-0.9, -0.5)

            else:
                 sentiment, polarity = analyze_sentiment_textblob(post.get('text', ''))

            # Update base post with new data
            post_id = f"{brand}_{i}_{datetime.now().timestamp()}"
            hashtags, mentions, keywords = extract_keywords(post.get('text', ''))
            
            p = Post(
                post_id=post_id,
                text=post.get('text', ''),
                platform=random.choice(profile['platforms']),
                brand=brand,
                timestamp=post.get('timestamp', datetime.now().isoformat()),
                likes=post.get('likes', 0),
                replies=post.get('replies', 0),
                sentiment=sentiment,
                polarity=polarity,
                hashtags=hashtags,
                keywords=keywords,
                location=random.choice(profile['locations']),
                user_segment=random.choice(profile['segments'])
            )
            posts.append(p)
            
        return posts

    def _get_brand_profile(self, brand: str) -> Dict[str, Any]:
        """Defines a simulated profile for different brands for realistic comparison."""
        brand_profiles = {
            "Tesla": {
                "sentiment_bias": 0.5, "positive_skew": 0.65,
                "keywords": ["EV", "Model 3", "Cybertruck", "autopilot", "Elon"],
                "locations": ["North America", "Europe", "Asia", "Unknown"],
                "platforms": ["Twitter", "Reddit"],
                "segments": ["Tech Enthusiast", "Investor", "General Public"]
            },
            "BMW": {
                "sentiment_bias": 0.3, "positive_skew": 0.55,
                "keywords": ["i4", "luxury", "iDrive", "service", "M series"],
                "locations": ["Europe", "North America", "Unknown"],
                "platforms": ["Facebook", "Instagram", "Twitter"],
                "segments": ["Luxury Buyer", "Auto Enthusiast", "General Public"]
            },
            "Nike": {
                "sentiment_bias": 0.6, "positive_skew": 0.70,
                "keywords": ["Jordan", "Air Max", "running", "sustainability", "shoes"],
                "locations": ["Asia", "North America", "Europe", "Unknown"],
                "platforms": ["Instagram", "Twitter", "Facebook"],
                "segments": ["Athlete", "Fashion Buyer", "Youth"]
            },
            "Mercedes": {
                "sentiment_bias": 0.2, "positive_skew": 0.50,
                "keywords": ["S-Class", "EQS", "dealer", "quality", "service"],
                "locations": ["Europe", "North America", "South America", "Unknown"],
                "platforms": ["LinkedIn", "Twitter", "Facebook"],
                "segments": ["Luxury Buyer", "Older Demographics", "Investor"]
            }
        }
        
        # Default profile if brand is new
        default_profile = {
            "sentiment_bias": 0.4, "positive_skew": 0.60,
            "keywords": ["product", "service", "experience", "quality"],
            "locations": ["North America", "Europe", "Unknown"],
            "platforms": ["Twitter", "Reddit", "Facebook"],
            "segments": ["General Public"]
        }
        
        return brand_profiles.get(brand, default_profile)

    def _get_cutoff_date(self, time_period: str) -> datetime:
        """Helper to determine the time cutoff for queries."""
        if time_period == '24h':
            return datetime.now() - timedelta(hours=24)
        elif time_period == '7d':
            return datetime.now() - timedelta(days=7)
        elif time_period == '30d':
            return datetime.now() - timedelta(days=30)
        return datetime.now() - timedelta(days=7)

    def insert_stream_post(self, stream_id: str, post: Post):
        """Inserts a new post into an active stream and the main database."""
        if stream_id in self.active_streams:
            # Add to stream buffer
            self.active_streams[stream_id]['data'].append(post)
            # Check for alerts
            self.check_sentiment_alerts(stream_id, post)
            # Also store in main database for persistence
            self.insert_post(post)
    
    def check_sentiment_alerts(self, stream_id: str, new_post: Post):
        """Enhanced alert checking logic for new posts."""
        if stream_id not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[stream_id]
        alerts = self.active_streams[stream_id].get('alerts', [])
        
        # Check negative sentiment threshold
        if new_post.sentiment == 'Negative' and new_post.polarity < thresholds.get('negative_threshold', -0.5):
            alerts.append({
                'type': 'high_negative_post',
                'severity': 'critical',
                'message': f"Critical negative post detected: {new_post.text[:50]}...",
                'timestamp': datetime.now().isoformat()
            })
            
        # Check for sudden spike in mentions (simulated by checking recent post count)
        recent_posts = self.active_streams[stream_id]['data'][-10:]
        mention_spike_threshold = thresholds.get('mention_spike', 5)
        
        if len(recent_posts) > mention_spike_threshold and len(recent_posts) > 1 and new_post == recent_posts[-1]:
             # Only trigger if the latest post is part of a cluster spike
            alerts.append({
                'type': 'mention_spike',
                'severity': 'warning',
                'message': f"Sudden spike: {len(recent_posts)} posts in a short window.",
                'timestamp': datetime.now().isoformat()
            })
            
        self.active_streams[stream_id]['alerts'] = alerts


# Initialize the global mock database instance
db = MockDatabase()

# ===========================
# SENTIMENT ANALYSIS FUNCTIONS
# ===========================

def analyze_sentiment_textblob(text: str) -> tuple[str, float]:
    """Sentiment analysis using TextBlob"""
    try:
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return 'Positive', polarity
        elif polarity < -0.1:
            return 'Negative', polarity
        else:
            return 'Neutral', polarity
    except:
        return 'Neutral', 0.0

def detect_emotions(text: str) -> Dict[str, int]:
    """Detect specific emotions in text based on keywords (simulated model)."""
    emotion_keywords = {
        'joy': ['happy', 'love', 'amazing', 'excellent', 'great', 'wonderful', 'excited', 'fantastic'],
        'anger': ['angry', 'hate', 'terrible', 'worst', 'awful', 'horrible', 'furious', 'annoyed'],
        'sadness': ['sad', 'disappointed', 'unhappy', 'depressed', 'unfortunate'],
        'surprise': ['wow', 'amazing', 'unexpected', 'shocked'],
        'fear': ['scared', 'worried', 'concerned', 'nervous', 'afraid', 'anxious']
    }
    
    text_lower = text.lower()
    emotions = {}
    
    for emotion, keywords in emotion_keywords.items():
        count = sum(1 for word in keywords if word in text_lower)
        if count > 0:
            emotions[emotion] = count
    
    return emotions

def extract_keywords(text: str) -> tuple[List[str], List[str], List[str]]:
    """Extract hashtags, mentions, and keywords."""
    hashtags = re.findall(r'#\w+', str(text))
    mentions = re.findall(r'@\w+', str(text))
    
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 
                  'her', 'was', 'one', 'our', 'out', 'this', 'that', 'with', 
                  'have', 'from', 'they', 'been', 'will', 'what', 'more', 'product', 'brand', 'service'}
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]
    
    return hashtags, mentions, keywords

# ===========================
# DATA GENERATION & REAL-TIME MOCK
# ===========================

def generate_sample_data(num_posts: int = 100) -> List[Dict[str, Any]]:
    """Generate sample social media posts for baseline data."""
    sample_posts = [
        "This product is amazing! Best purchase ever! #love #awesome #tesla",
        "Terrible customer service. Very disappointed. #fail #nike",
        "It's okay, nothing special but does the job.#infosys",
        "Love the new features! Keep up the great work! @infynd_data",
        "Worst experience. Will never buy again. #disappointed",
        "Just got the new item, the quality seems questionable.",
        "The price point is surprisingly good for what you get.",
        "Neutral feeling about the update, neither great nor bad."
    ]
    
    platforms = ['Twitter', 'Facebook', 'Instagram', 'Reddit', 'LinkedIn']
    locations = ['North America', 'Europe', 'Asia', 'South America', 'Unknown']
    user_segments = ["Tech Enthusiast", "Investor", "General Public", "Luxury Buyer"]
    
    data = []
    for i in range(num_posts):
        post_text = random.choice(sample_posts)
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 72), minutes=random.randint(0, 60))
        
        sentiment, polarity = analyze_sentiment_textblob(post_text)
        hashtags, mentions, keywords = extract_keywords(post_text)
        emotions = detect_emotions(post_text)
        
        data.append({
            'post_id': str(i + 1),
            'text': post_text,
            'platform': random.choice(platforms),
            'timestamp': timestamp.isoformat(),
            'likes': random.randint(0, 500),
            'retweets': random.randint(0, 100),
            'replies': random.randint(0, 50),
            'sentiment': sentiment,
            'polarity': polarity,
            'hashtags': hashtags,
            'mentions': mentions,
            'keywords': keywords,
            'emotions': emotions,
            'location': random.choice(locations),
            'language': 'en',
            'user_segment': random.choice(user_segments)
        })
    
    return data

def start_realtime_stream_mock(brand_name: str, keywords: List[str], platform: str) -> Dict[str, Any]:
    """Mocks starting a real-time stream via API search and initializes stream data in MockDB."""
    stream_id = f"{brand_name}_{int(datetime.now().timestamp())}_{random.randint(100, 999)}"
    
    # Simulate fetching initial 20 posts from the 'stream'
    mock_posts_data = generate_sample_data(20)
    
    # Process and convert to Post objects
    initial_posts: List[Post] = []
    for i, data in enumerate(mock_posts_data):
        post_id = f"{stream_id}_{i}"
        
        # Introduce very high negative post to test immediate alerts
        if i == 1: 
            data['text'] = f"The {brand_name} launch is an absolute disaster! Shameful. #worstlaunch"
            data['sentiment'], data['polarity'] = 'Negative', -0.95
        
        p = Post(
            post_id=post_id,
            brand=brand_name,
            platform=platform,
            **{k: v for k, v in data.items() if k in Post.__dataclass_fields__}
        )
        initial_posts.append(p)
        db.insert_post(p) # Insert into historical DB
        
    db.active_streams[stream_id] = {
        'brand': brand_name,
        'platform': platform,
        'keywords': keywords,
        'data': initial_posts, # Current buffer of stream posts
        'status': 'active',
        'start_time': datetime.now().isoformat(),
        'alerts': []
    }
    
    # Run alert checks on initial data
    for post in initial_posts:
        db.check_sentiment_alerts(stream_id, post)

    return {'success': True, 'stream_id': stream_id}

# ===========================
# ANALYSIS FUNCTIONS
# ===========================

def calculate_metrics(data: List[Post]) -> Dict[str, Any]:
    """Calculate comprehensive sentiment metrics."""
    if not data:
        return {'total_posts': 0, 'positive_count': 0, 'negative_count': 0, 'neutral_count': 0,
                'positive_pct': 0, 'negative_pct': 0, 'neutral_pct': 0,
                'avg_polarity': 0.0, 'total_engagement': 0}
    
    df = pd.DataFrame([p.__dict__ for p in data])
    total = len(df)
    
    positive = len(df[df['sentiment'] == 'Positive'])
    negative = len(df[df['sentiment'] == 'Negative'])
    neutral = len(df[df['sentiment'] == 'Neutral'])
    
    return {
        'total_posts': total,
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'positive_pct': round((positive / total * 100) if total > 0 else 0, 1),
        'negative_pct': round((negative / total * 100) if total > 0 else 0, 1),
        'neutral_pct': round((neutral / total * 100) if total > 0 else 0, 1),
        'avg_polarity': round(df['polarity'].mean(), 3),
        'total_engagement': int(df['likes'].sum() + df.get('retweets', pd.Series([0])).sum())
    }

def analyze_brand_sentiment(brand_name: str, competitors: List[str], time_period: str) -> Dict[str, Any]:
    """Comprehensive brand sentiment analysis with competitor comparison."""
    all_brands = [brand_name] + competitors
    brand_analysis = {}
    total_mentions = 0
    
    for brand in all_brands:
        # Data is fetched/generated from MockDatabase
        posts = db.get_posts(brand, time_period)
        metrics = calculate_metrics(posts)
        
        brand_analysis[brand] = {
            'data': [p.__dict__ for p in posts],
            'metrics': metrics,
            'sentiment_score': metrics.get('avg_polarity', 0),
            'trend': calculate_sentiment_trend(posts),
            'share_of_voice': 0
        }
        total_mentions += metrics.get('total_posts', 0)
    
    # Calculate share of voice
    for brand in brand_analysis:
        mentions = brand_analysis[brand]['metrics']['total_posts']
        brand_analysis[brand]['share_of_voice'] = (mentions / total_mentions * 100) if total_mentions > 0 else 0
    
    return brand_analysis

def calculate_sentiment_trend(data: List[Post]) -> str:
    """Calculate sentiment trend (improving/declining/stable) based on two halves."""
    if len(data) < 20:
        return 'stable'
    
    df = pd.DataFrame([p.__dict__ for p in data])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Split into two halves: oldest (first_half) vs newest (second_half)
    mid = len(df) // 2
    first_half_avg = df.iloc[:mid]['polarity'].mean()
    second_half_avg = df.iloc[mid:]['polarity'].mean()
    
    diff = second_half_avg - first_half_avg
    
    if diff > 0.1:
        return 'improving'
    elif diff < -0.1:
        return 'declining'
    else:
        return 'stable'

def analyze_by_region(data: List[Post]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Analyze sentiment by geographic region and demographic segments."""
    regional_data = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0})
    demographics = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0})
    
    for post in data:
        region = post.location
        segment = post.user_segment
        sentiment = post.sentiment
        
        # Regional
        regional_data[region][sentiment.lower()] += 1
        regional_data[region]['total'] += 1
        
        # Demographic (by segment type, simulating age/gender for realism)
        demographics[segment][sentiment.lower()] += 1
        demographics[segment]['total'] += 1
    
    # Calculate percentages for Regional
    for region in regional_data:
        total = regional_data[region]['total']
        if total > 0:
            regional_data[region]['positive_pct'] = round(regional_data[region]['positive'] / total * 100, 1)
            regional_data[region]['negative_pct'] = round(regional_data[region]['negative'] / total * 100, 1)
    
    # Calculate percentages for Demographics
    for segment in demographics:
        total = demographics[segment]['total']
        if total > 0:
            demographics[segment]['positive_pct'] = round(demographics[segment]['positive'] / total * 100, 1)
            demographics[segment]['negative_pct'] = round(demographics[segment]['negative'] / total * 100, 1)
    
    return dict(regional_data), dict(demographics)

def analyze_trending_topics(data: List[Post], time_window: str) -> Dict[str, Any]:
    """Analyze trending keywords and hashtags with temporal analysis."""
    df = pd.DataFrame([p.__dict__ for p in data])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Get recent data based on time window
    cutoff = db._get_cutoff_date(time_window)
    recent_data = df[df['timestamp'] >= cutoff]
    
    # Analyze hashtags with sentiment
    hashtag_analysis = defaultdict(lambda: {'count': 0, 'positive': 0, 'negative': 0, 'neutral': 0})
    
    for _, post in recent_data.iterrows():
        for hashtag in post['hashtags']:
            hashtag_analysis[hashtag]['count'] += 1
            hashtag_analysis[hashtag][post['sentiment'].lower()] += 1
    
    # Calculate sentiment percentages and scores
    for tag in hashtag_analysis:
        total = hashtag_analysis[tag]['count']
        if total > 0:
            hashtag_analysis[tag]['positive_pct'] = round(hashtag_analysis[tag]['positive'] / total * 100, 1)
            hashtag_analysis[tag]['negative_pct'] = round(hashtag_analysis[tag]['negative'] / total * 100, 1)
            hashtag_analysis[tag]['sentiment_score'] = round((hashtag_analysis[tag]['positive'] - hashtag_analysis[tag]['negative']) / total, 3)
        else:
            hashtag_analysis[tag]['positive_pct'] = 0
            hashtag_analysis[tag]['negative_pct'] = 0
            hashtag_analysis[tag]['sentiment_score'] = 0

    # Sort by count and filter to top 20
    trending_hashtags = sorted(hashtag_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
    
    return {
        'trending_hashtags': [{'tag': tag, **data} for tag, data in trending_hashtags],
        'time_window': time_window,
        'total_analyzed': len(recent_data)
    }

def analyze_keyword_evolution(data: List[Post], keyword: str) -> List[Dict[str, Any]]:
    """Track how sentiment about a specific keyword evolves over time."""
    df = pd.DataFrame([p.__dict__ for p in data])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Filter posts containing keyword
    keyword_posts = df[df['text'].str.contains(keyword, case=False, na=False)]
    
    # Group by time periods (daily for simplicity)
    keyword_posts['date'] = keyword_posts['timestamp'].dt.date
    daily_sentiment = keyword_posts.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
    
    evolution = []
    for date, row in daily_sentiment.iterrows():
        total = row.sum()
        evolution.append({
            'date': str(date),
            'positive': int(row.get('Positive', 0)),
            'negative': int(row.get('Negative', 0)),
            'neutral': int(row.get('Neutral', 0)),
            'total': int(total),
            'sentiment_score': round((row.get('Positive', 0) - row.get('Negative', 0)) / total if total > 0 else 0, 3)
        })
    
    return evolution

def generate_ai_summary(data: List[Post], brand_name: str) -> str:
    """
    Mocks an interaction with an advanced LLM to generate a sophisticated
    executive summary and recommendations.
    """
    if not data:
        return "No data available for summarization."
    
    # 1. Gather comprehensive inputs
    metrics = calculate_metrics(data)
    regional, demographics = analyze_by_region(data)
    trending = analyze_trending_topics(data, '7d')
    
    # 2. Structure a detailed prompt (as if for an LLM)
    prompt_context = f"""
    You are a Senior Brand Intelligence Analyst. Generate a detailed, actionable
    executive summary for the brand: **{brand_name}**.

    --- DATA ANALYSIS SUMMARY ---
    1. Overall Metrics:
        - Total Mentions: {metrics['total_posts']}
        - Average Polarity Score: {metrics['avg_polarity']:.3f}
        - Sentiment Distribution: {metrics['positive_pct']}% Positive, {metrics['negative_pct']}% Negative.
        - Engagement Score: {metrics['total_engagement']}
        - Trend: {calculate_sentiment_trend(data).upper()}

    2. Key Topics/Issues (Top 5 Hashtags):
        {json.dumps(trending['trending_hashtags'][:5], indent=2)}

    3. Regional Performance (Top 3 Regions):
        {json.dumps({r: regional[r] for r in list(regional.keys())[:3] if r != 'Unknown'}, indent=2)}

    4. Top Negative Drivers (Find 3 highly negative posts):
        {json.dumps([p.__dict__ for p in data if p.sentiment == 'Negative'][:3], indent=2)}

    --- TASK ---
    Based on the data above, generate a summary covering:
    - Overall Brand Health (1 sentence)
    - Primary Positive and Negative Drivers.
    - Regional High/Low points.
    - Two specific, actionable marketing recommendations to improve the Negative Score and capitalize on the Positive Drivers.
    """
    
    # 3. Simulate LLM Output based on context (since we can't call an actual LLM here)
    trend = calculate_sentiment_trend(data)
    health = "strong and growing" if trend == 'improving' and metrics['avg_polarity'] > 0.1 else "stable but facing minor headwinds"
    
    top_positive_topic = trending['trending_hashtags'][0]['tag'] if trending['trending_hashtags'] else 'Product Quality'
    top_negative_topic = "Customer Service issues"
    
    simulated_summary = f"""
🎯 EXECUTIVE SUMMARY — {brand_name} Brand Health

The current brand health index is {health}.  
We observe a net positive sentiment score of {metrics['avg_polarity']:.3f}, despite heated discussion in the market.  
The dominant trend is {trend.upper()}.

Key Drivers of Sentiment

- Positive Driver: Conversations around #{top_positive_topic} are driving favorable buzz, especially among the {list(demographics.keys())[0]} demographic.  
- Negative Driver: The topic {top_negative_topic} is a recurring friction point. A sample negative post (“{data[1].text[:30]}...”) highlights issues with response time and resolution.


Regional Performance Snapshot

- {list(regional.keys())[0]} region leads with strong positivity ({regional[list(regional.keys())[0]].get('positive_pct', 0)}%).  
- {list(regional.keys())[1]} region lags, showing higher neutral/negative sentiment.

Actionable Recommendations

1. Amplify the positive momentum by promoting user stories and content around {top_positive_topic} in {list(regional.keys())[0]}.  
2. Address recurring complaints immediately — consider enforcing a 24-hour response SLA and flagging posts around {top_negative_topic} for escalation.  
3. Perform deeper analysis: break down sentiment by topic cluster, user segment, and platform to surface root causes.  
4. Tailor messaging by region: customize your communication and campaigns in underperforming regions to address local concerns.  
5. Monitor shifts & act fast: set up alerts for sudden negative sentiment spikes or topic surges.

"""

    
    return simulated_summary

# ===========================
# FLASK ROUTES
# ===========================

@app.route('/')
def index():
    """Restored the root route to serve the index.html content."""
    # This assumes index.html is in the same directory, which is necessary for the Canvas environment
    return render_template('index.html')

@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """Get sample data for initial dashboard load."""
    brand = 'SampleBrand'
    # Use MockDB to get posts, which will generate them if not present
    posts = db.get_posts(brand, '7d')
    metrics = calculate_metrics(posts)
    regional, demographics = analyze_by_region(posts)
    trending = analyze_trending_topics(posts, '24h')
    
    return jsonify({
        'success': True,
        'data': [p.__dict__ for p in posts],
        'metrics': metrics,
        'regional': regional,
        'demographics': demographics,
        'trending': trending
    })

@app.route('/api/brand-analysis', methods=['POST'])
def analyze_brand():
    """Comprehensive brand analysis for a single brand."""
    brand_name = request.json.get('brand_name')
    time_period = request.json.get('time_period', '7d')
    
    if not brand_name:
        return jsonify({'success': False, 'error': 'Brand name required'})
    
    # Use the unified analysis function, treating it as a single brand analysis
    analysis = analyze_brand_sentiment(brand_name, [], time_period)
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

@app.route('/api/start-realtime', methods=['POST'])
def start_realtime_monitoring():
    """Start real-time sentiment monitoring mock."""
    brand_name = request.json.get('brand_name')
    keywords = request.json.get('keywords', [])
    platform = request.json.get('platform', 'twitter')
    
    if not brand_name:
        return jsonify({'success': False, 'error': 'Brand name required'})
    
    result = start_realtime_stream_mock(brand_name, keywords, platform)
    
    return jsonify(result)

@app.route('/api/realtime-data/<stream_id>', methods=['GET'])
def get_realtime_data(stream_id: str):
    """Get real-time stream data from MockDB."""
    if stream_id not in db.active_streams:
        return jsonify({'success': False, 'error': 'Stream not found'})
    
    stream_data = db.active_streams[stream_id]
    
    # Simulate a small amount of new data arriving every few seconds
    if random.random() < 0.7: # 70% chance of new data
        new_post_data = generate_sample_data(random.randint(1, 3))[0]
        new_post = Post(
            post_id=f"live_{stream_id}_{datetime.now().timestamp()}",
            brand=stream_data['brand'],
            platform=stream_data['platform'],
            **{k: v for k, v in new_post_data.items() if k in Post.__dataclass_fields__}
        )
        db.insert_stream_post(stream_id, new_post)
        
    current_posts = stream_data['data']
    metrics = calculate_metrics(current_posts)
    trending = analyze_trending_topics(current_posts, '1h')
    
    return jsonify({
        'success': True,
        'data': [p.__dict__ for p in current_posts],
        'metrics': metrics,
        'trending': trending,
        'alerts': stream_data.get('alerts', []),
        'status': stream_data['status']
    })

@app.route('/api/stop-realtime/<stream_id>', methods=['POST'])
def stop_realtime_monitoring(stream_id: str):
    """Stop real-time monitoring mock."""
    if stream_id in db.active_streams:
        db.active_streams[stream_id]['status'] = 'stopped'
        return jsonify({'success': True, 'message': 'Stream stopped'})
    return jsonify({'success': False, 'error': 'Stream not found'})

@app.route('/api/set-alerts', methods=['POST'])
def set_alerts():
    """Configure alert thresholds."""
    stream_id = request.json.get('stream_id')
    thresholds = request.json.get('thresholds', {})
    
    if not stream_id:
        return jsonify({'success': False, 'error': 'Stream ID required'})
    
    db.alert_thresholds[stream_id] = thresholds
    return jsonify({'success': True})

@app.route('/api/regional-analysis', methods=['POST'])
def get_regional_analysis():
    """Get regional and demographic sentiment analysis."""
    # The frontend sends post data as a list of dictionaries, convert back to Post objects
    data_dicts = request.json.get('data', [])
    data = [Post(**d) for d in data_dicts]
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    regional, demographics = analyze_by_region(data)
    
    return jsonify({
        'success': True,
        'regional': regional,
        'demographics': demographics
    })

@app.route('/api/trending-analysis', methods=['POST'])
def get_trending_analysis():
    """Get trending topics and hashtag analysis."""
    data_dicts = request.json.get('data', [])
    data = [Post(**d) for d in data_dicts]
    time_window = request.json.get('time_window', '24h')
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    trending = analyze_trending_topics(data, time_window)
    
    return jsonify({
        'success': True,
        'trending': trending
    })

@app.route('/api/keyword-evolution', methods=['POST'])
def get_keyword_evolution():
    """Track keyword sentiment evolution over time."""
    data_dicts = request.json.get('data', [])
    data = [Post(**d) for d in data_dicts]
    keyword = request.json.get('keyword', '')
    
    if not data or not keyword:
        return jsonify({'success': False, 'error': 'Data and keyword required'})
    
    evolution = analyze_keyword_evolution(data, keyword)
    
    return jsonify({
        'success': True,
        'keyword': keyword,
        'evolution': evolution
    })

@app.route('/api/ai-summary', methods=['POST'])
def get_ai_summary():
    """Generate AI-powered insights summary using the enhanced mock."""
    data_dicts = request.json.get('data', [])
    data = [Post(**d) for d in data_dicts]
    brand_name = request.json.get('brand_name', 'Brand')
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    summary = generate_ai_summary(data, brand_name)
    
    return jsonify({
        'success': True,
        'summary': summary
    })

@app.route('/api/competitor-compare', methods=['POST'])
def compare_competitors():
    """Compare multiple brands side-by-side using realistic (simulated) data."""
    brands = request.json.get('brands', [])
    time_period = request.json.get('time_period', '7d')
    
    if len(brands) < 2:
        return jsonify({'success': False, 'error': 'At least 2 brands required'})
    
    main_brand = brands[0]
    competitors = brands[1:]
    
    # This call now uses the MockDB, which generates varied data for each brand
    analysis = analyze_brand_sentiment(main_brand, competitors, time_period)
    
    return jsonify({
        'success': True,
        'comparison': analysis
    })

# --- Main Execution ---

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Enhanced Brand Sentiment Analysis Platform")
    print("=" * 70)
    print("✨ Core Enhancements:")
    print("  • MockDatabase for persistence simulation.")
    print("  • Structured Post data object.")
    print("  • More realistic, varied data generation for competitors.")
    print("  • Sophisticated LLM prompt simulation for AI Summary.")
    print("=" * 70)
    print("🌐 Server: http://localhost:5001")
    print("⚡ Press Ctrl+C to stop")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5001)
