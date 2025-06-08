# -*- coding: utf-8 -*-

# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
 from youtube_transcript_api import YouTubeTranscriptApi

import googleapiclient.discovery
import googleapiclient.errors

from dotenv import load_dotenv

load_dotenv()


def main(username):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.

    api_service_name = "youtube"
    api_version = "v3"

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=os.getenv("YOUTUBE_API_KEY"))

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
        id=channel_id
    )
    chanel_response = chanel_reponse.execute()

    upload_id = chanel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    playlist_response = youtube.playlistItems().list(
        part='snippet',
        playlistId=upload_id,
        maxResults=1
    )
    playlist_response = playlist_response.execute()

   
    
    video = playlist_response['items'][0]['snippet']
    
    transcript = YouTubeTranscriptApi.get_transcript(video['resourceId']['videoId'])


    transcript_text = ""
    for entry in transcript:
        transcript_text += entry['text'] + " "

    with open('transcript.txt', 'w', encoding='utf-8') as f:
        f.write(transcript_text)
        
if __name__ == "__main__":
    main()