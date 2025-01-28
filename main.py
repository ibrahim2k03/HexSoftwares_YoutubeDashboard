import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from googleapiclient.discovery import build
import isodate
import numpy as np
import re

st.set_page_config(layout="wide")
api_key = st.secrets["api_key"]["myAPIKey"]
API = api_key

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        
        @media screen and (max-width: 768px) {
            .block-container {
                padding: 1rem !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

youtube = build("youtube", "v3", developerKey=API)

def getChennelID(url):
    pattern_channel_id = r"youtube\.com\/channel\/([a-zA-Z0-9_-]+)"
    pattern_custom_handle = r"youtube\.com\/@([a-zA-Z0-9_-]+)"
    
    match_channel_id = re.search(pattern_channel_id, url)
    if match_channel_id:
        return match_channel_id.group(1)
    
    match_custom_handle = re.search(pattern_custom_handle, url)
    if match_custom_handle:
        custom_handle = match_custom_handle.group(1)
        try:
            request = youtube.search().list(
                part="snippet",
                q=custom_handle,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            if "items" in response and len(response["items"]) > 0:
                return response["items"][0]["snippet"]["channelId"]
            else:
                st.error(f"No channel found for handle: @{custom_handle}")
                return None
        except Exception as e:
            st.error(f"Error resolving custom handle: {e}")
            return None
    
    st.error("Invalid YouTube channel URL. Please provide a valid URL.")
    return None

def channelStats(channelID):
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channelID
        )
        response = request.execute()
        stats = response["items"][0]["statistics"]
        
        # Fetch total likes and comments from the top videos
        topVideos = getTopVideos(channelID)
        total_likes = sum(video['Likes'] for video in topVideos)
        total_comments = sum(video['Comments'] for video in topVideos)
        
        return {
            "Subscribers": int(stats["subscriberCount"]),
            "Total Videos": int(stats["videoCount"]),
            "Likes from Views": f"{(total_likes / int(stats['viewCount'])) * 100:.2f}%",
            "Average Views per Video": int(stats["viewCount"]) / int(stats["videoCount"]),
            "Average Likes per Video": total_likes / int(stats["videoCount"]),
            "Average Comments per Video": total_comments / int(stats["videoCount"]),
            }
    except Exception as e:
        st.error(f"Error fetching channel data: {e}")
        return None
    
def getTopVideos(channelID):
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channelID,
            order="viewCount",
            maxResults=50  
        )
        response = request.execute()
        
        videoData = []
        for video in response["items"]:
            videoID = video["id"].get("videoId")
            if not videoID:
                continue
            
            videoRequest = youtube.videos().list(
                part="statistics,contentDetails",
                id=videoID
            )
            videoResponse = videoRequest.execute()
            
            if "items" in videoResponse and len(videoResponse["items"]) > 0:
                stats = videoResponse["items"][0]["statistics"]
                duration = isodate.parse_duration(videoResponse["items"][0]["contentDetails"]["duration"]).total_seconds()
                
                videoData.append({
                    "Title": video["snippet"]["title"],
                    "Views": int(stats.get("viewCount", 0)),
                    "Likes": int(stats.get("likeCount", 0)),
                    "Comments": int(stats.get("commentCount", 0)),
                    "Duration (s)": duration,
                    "Like-to-View Ratio": round(int(stats.get("likeCount", 0)) / int(stats.get("viewCount", 1)), 5),
                    "Comment-to-View Ratio": round(int(stats.get("commentCount", 0)) / int(stats.get("viewCount", 1)), 5)
                })
        return videoData
    except Exception as e:
        st.error(f"Error fetching top videos: {e}")
        return []

# ---------------------- User Interface ---------------------- #
st.title("📊 YouTube Data Dashboard")

channelURL = st.sidebar.text_input("Enter YouTube Channel URL", "https://www.youtube.com/@Fireship")

if st.sidebar.button("Get Data"):
    channelID = getChennelID(channelURL)
    
    if channelID:
        stats = channelStats(channelID)
        
        if stats:
            st.subheader("📌 Channel Statistics")
            
            cols = st.columns(2) if st.session_state.get("mobile") else st.columns(6)

            cols[0].metric("Subscribers", stats["Subscribers"])
            cols[1].metric("Total Videos", stats["Total Videos"])
            cols[2].metric("Likes from Views", stats["Likes from Views"])
            cols[3].metric("Avg Views per Video", round(stats["Average Views per Video"]))
            cols[4].metric("Avg Likes per Video", round(stats["Average Likes per Video"]))
            cols[5].metric("Avg Comments per Video", round(stats["Average Comments per Video"]))
        
        topVideos = getTopVideos(channelID)
        
        if topVideos:
            st.subheader("🎬 Top 50 Videos")
            videosDf = pd.DataFrame(topVideos)
            st.dataframe(videosDf)
            
            top10_videosDf = videosDf.nlargest(10, 'Views')

            # Bar Chart: Top 10 Performing Videos 
            fig1 = px.bar(top10_videosDf, x="Title", y="Views", title="Top 10 Videos", text="Views", color="Likes")
            fig1.update_traces(texttemplate='%{text}', textposition='outside')
            fig1.update_layout(autosize=True, width=None, height=750)
            st.plotly_chart(fig1)
            
            # Scatter Plot: Likes vs. Views
            fig2 = px.scatter(videosDf, x="Views", y="Likes", size="Comments", title="Views vs. Likes", hover_data=["Title"])
            fig2.update_layout(autosize=True, width=None, height=750)
            st.plotly_chart(fig2)
            
            # Heatmap: Correlation between Views, Likes, Comments, and Duration
            dfCorr = videosDf[["Views", "Likes", "Comments", "Duration (s)"]].corr()
            fig3 = px.imshow(dfCorr, text_auto=True, title="🔥 Heatmap: Correlation between Video Stats")
            fig3.update_layout(autosize=True, width=None, height=750)
            st.plotly_chart(fig3)