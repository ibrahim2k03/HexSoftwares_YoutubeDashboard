import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from googleapiclient.discovery import build
import isodate
import numpy as np

st.set_page_config(layout="wide")
api_key = st.secrets["api_key"]["myAPIKey"]

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

API = api_key 
youtube = build("youtube", "v3", developerKey=API)

def channelStats(channelID):
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channelID
        )
        response = request.execute()
        stats = response["items"][0]["statistics"]
        return {
            "Subscribers": int(stats["subscriberCount"]),
            "Total Views": int(stats["viewCount"]),
            "Total Videos": int(stats["videoCount"]),
            "Subscribers from Views": int(stats["subscriberCount"])/int(stats["viewCount"]),
            "Average Views per Video": int(stats["viewCount"]) / int(stats["videoCount"]),
            "Views per Subscriber": int(stats["viewCount"]) / int(stats["subscriberCount"]),
            "Engagement Rate": (int(stats.get("likeCount", 0)) + int(stats.get("commentCount", 0))) / int(stats["viewCount"])
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
            maxResults=100  
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
st.title("📊 HexSoftwares YouTube Data Dashboard")

channelID = st.sidebar.text_input("Enter YouTube Channel ID", "UCphTF9wHwhCt-BzIq-s4V-g")

if st.sidebar.button("Get Data"):
    stats = channelStats(channelID)
    
    if stats:
        st.subheader("📌 Channel Statistics")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Subscribers", stats["Subscribers"])
        col2.metric("Total Views", stats["Total Views"])
        col3.metric("Total Videos", stats["Total Videos"])
        col4.metric("Avg Views per Video", round(stats["Average Views per Video"]))
        col5.metric("Views per Subscriber", round(stats["Views per Subscriber"], 2))
        col6.metric("Engagement Rate", round(stats["Engagement Rate"], 5))
    
    topVideos = getTopVideos(channelID)
    
    if topVideos:
        st.subheader("🎬 Top 100 Videos by Views")
        df_videos = pd.DataFrame(topVideos)
        st.dataframe(df_videos)
        
        # Additional statistics
        df_videos['Log Views'] = np.log1p(df_videos['Views'])
        df_videos['Log Likes'] = np.log1p(df_videos['Likes'])
        
        # Bar Chart: Top Performing Videos by Views
        fig1 = px.bar(df_videos, x="Title", y="Views", title="Top Performing Videos", text="Views", color="Likes")
        fig1.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig1)
        
        # Scatter Plot: Likes vs. Views
        fig2 = px.scatter(df_videos, x="Views", y="Likes", size="Comments", title="Views vs. Likes", hover_data=["Title"])
        st.plotly_chart(fig2)
        
        # Bar Chart: Video Duration vs. Views
        fig3 = px.bar(df_videos, x="Title", y="Views", title="Video Duration vs. Views", color="Duration (s)", text="Views")
        fig3.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig3)
        
        # Heatmap: Correlation between Views, Likes, Comments, and Duration
        dfCorr = df_videos[["Views", "Likes", "Comments", "Duration (s)"]].corr()
        fig4 = px.imshow(dfCorr, text_auto=True, title="🔥 Heatmap: Correlation between Video Stats")
        st.plotly_chart(fig4)
        
        # Distribution Plot: Log-transformed Views and Likes
        fig5 = ff.create_distplot([df_videos['Log Views'], df_videos['Log Likes']], ['Log Views', 'Log Likes'], show_hist=False)
        fig5.update_layout(title="📊 Distribution of Log-Transformed Views and Likes")
        st.plotly_chart(fig5)
