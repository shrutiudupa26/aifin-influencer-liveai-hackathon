# -*- coding: utf-8 -*-

# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
from youtube_transcript_api import YouTubeTranscriptApi

import googleapiclient.discovery
import googleapiclient.errors

from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import iso8601

load_dotenv()


def main(username):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.

    api_service_name = "youtube"
    api_version = "v3"

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, 
        developerKey=os.getenv("YOUTUBE_API_KEY"))

    request = youtube.search().list(
            q=username,
            type='channel',
            part='snippet',
            maxResults=5
            )
   
    response = request.execute() 
    channel_id = response['items'][0]['snippet']['channelId']
    

    chanel_reponse = youtube.channels().list(
        part='contentDetails',
        id=channel_id,
    )

    chanel_response = chanel_reponse.execute()
    upload_id = chanel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    now = datetime.now(timezone.utc)
    min_date = now - timedelta(days=150)  # 5 months ago
    max_date = now - timedelta(days=30)

    next_page_token = None
    videos = []

    while True:
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=upload_id,
            maxResults=50,
            pageToken=next_page_token
        )

        playlist_response = playlist_response.execute()

        for item in playlist_response['items']:
            snippet = item['snippet']
            published_at = iso8601.parse_date(snippet['publishedAt'])

            if min_date <= published_at <= max_date:
                print(snippet['title'])
                video_id = snippet['resourceId']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append({
                    'title': snippet['title'],
                    'url': video_url,
                    'video_id': video_id,
                    'published_at': published_at.isoformat()
                })
            
            if published_at < min_date:
                break
            
          
        next_page_token = playlist_response.get('nextPageToken')

        if not next_page_token:
            break

        if len(videos) >= 20:
            break
    
    transcript_metadata = {}
    for v in videos:
        # transcript = YouTubeTranscriptApi.get_transcript(v['video_id'])
        transcript_metadata[v['video_id']] = {
            'title': v['title'],
            'url': f"https://www.youtube.com/watch?v={v['video_id']}",
            'published_at': v['published_at']
        }
   
    return transcript_metadata
        

    # transcript_text = ""
    # for entry in transcript:
    #     transcript_text += entry['text'] + " "

    # with open('transcript.txt', 'w', encoding='utf-8') as f:
    #     f.write(transcript_text)
        
if __name__ == "__main__":
    username = ["everything money","New Money"]
    data = []
    for user in username:
        data.append(main(user))

    print(data)