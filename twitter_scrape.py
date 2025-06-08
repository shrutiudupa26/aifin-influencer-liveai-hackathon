import os
import json
import time
import datetime
from dateutil.relativedelta import relativedelta
import tweepy
from tweepy import TooManyRequests

def get_client():
    """Initialize Tweepy client without automatic rate-limit sleeping."""
    bearer = os.environ.get("TWITTER_BEARER_TOKEN")
    if not bearer:
        bearer = input("Enter your Twitter Bearer Token: ").strip()
    return tweepy.Client(
        bearer_token=bearer,
        wait_on_rate_limit=False
    )

def fetch_recent(keyword, days_back, max_tweets, client):
    """
    Fetch up to `max_tweets` from the past `days_back` days using Recent Search.
    - If max_tweets ≤ 100: use a single API call (one request).
    - Otherwise: paginate in batches of 100, throttling 1s/page.
    Stops immediately on a 429 and returns whatever was fetched.
    """
    # compute valid start_time (clamped to 7 days ago)
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(days=7)
    requested = now - datetime.timedelta(days=days_back)
    start_time = max(requested, cutoff).isoformat("T") + "Z"
    query = f"{keyword} lang:en -is:retweet"

    # Single-request path for small batches
    if max_tweets <= 100:
        try:
            resp = client.search_recent_tweets(
                query=query,
                start_time=start_time,
                tweet_fields=["created_at","text","author_id"],
                expansions=["author_id"],
                user_fields=["username"],
                max_results=max_tweets
            )
        except TooManyRequests:
            print("⚠️ Rate limit hit on single call—please wait ~15 minutes and retry.")
            return []

        tweets = []
        if resp.data:
            users = {u.id: u for u in resp.includes.get("users", [])}
            for t in resp.data:
                u = users.get(t.author_id)
                tweets.append({
                    "username": u.username if u else None,
                    "date":     t.created_at.isoformat(),
                    "content":  t.text.replace("\n"," ")
                })
        return tweets

    # Paginated path for larger batches
    collected = []
    try:
        paginator = tweepy.Paginator(
            client.search_recent_tweets,
            query=query,
            start_time=start_time,
            tweet_fields=["created_at","text","author_id"],
            expansions=["author_id"],
            user_fields=["username"],
            max_results=100
        )
        for page in paginator:
            if not page.data:
                break

            users = {u.id: u for u in page.includes.get("users", [])}
            for t in page.data:
                u = users.get(t.author_id)
                collected.append({
                    "username": u.username if u else None,
                    "date":     t.created_at.isoformat(),
                    "content":  t.text.replace("\n"," ")
                })
                if len(collected) >= max_tweets:
                    return collected

            # throttle to avoid exhausting quota too quickly
            time.sleep(1)

    except TooManyRequests:
        print(f"⚠️ Rate limit hit after collecting {len(collected)} tweets; returning partial results.")

    return collected

def fetch_full_archive(keyword, months_back, max_tweets, client):
    """
    Fetch up to `max_tweets` from the past `months_back` months using Full-archive Search.
    Requires Elevated or Academic Research access.
    """
    start_time = (datetime.datetime.utcnow() - relativedelta(months=months_back))\
                 .isoformat("T") + "Z"
    query = f"{keyword} lang:en -is:retweet"
    collected = []

    try:
        paginator = tweepy.Paginator(
            client.search_all_tweets,
            query=query,
            start_time=start_time,
            tweet_fields=["created_at","text","author_id"],
            expansions=["author_id"],
            user_fields=["username"],
            max_results=100
        )
        for page in paginator:
            if not page.data:
                break

            users = {u.id: u for u in page.includes.get("users", [])}
            for t in page.data:
                u = users.get(t.author_id)
                collected.append({
                    "username": u.username if u else None,
                    "date":     t.created_at.isoformat(),
                    "content":  t.text.replace("\n"," ")
                })
                if len(collected) >= max_tweets:
                    return collected

            time.sleep(1)

    except TooManyRequests:
        print(f"⚠️ Rate limit hit after collecting {len(collected)} tweets; returning partial results.")

    return collected

def main():
    client = get_client()
    kw    = input("Keyword or ticker (e.g. $AAPL): ").strip()
    days  = int(input("Past days to include (≤7 for recent): ").strip())
    total = int(input("Max tweets to fetch: ").strip())

    if days <= 7:
        print(f"Using Recent Search (last {days} days)…")
        data = fetch_recent(kw, days, total, client)
    else:
        months = days // 30
        print(f"Using Full-archive Search (last {months} months)…")
        data = fetch_full_archive(kw, months, total, client)

    print(f"Done: collected {len(data)} tweets.")
    with open("tweets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to tweets.json")

if __name__ == "__main__":
    main()