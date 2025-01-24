import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
import isodate

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        /* Reduce the default padding/margins */
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





API = "" 

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
            "Average Views per Video": int(stats["viewCount"]) / int(stats["videoCount"])
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
            videoID = video["id"]["videoId"]
            
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
                    "Views": int(stats["viewCount"]),
                    "Likes": int(stats.get("likeCount", 0)),
                    "Comments": int(stats.get("commentCount", 0)),
                    "Duration (s)": duration,
                    "Like-to-View Ratio": round(int(stats.get("likeCount", 0)) / int(stats["viewCount"]), 5) if int(stats["viewCount"]) > 0 else 0,
                    "Comment-to-View Ratio": round(int(stats.get("commentCount", 0)) / int(stats["viewCount"]), 5) if int(stats["viewCount"]) > 0 else 0
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
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Subscribers", stats["Subscribers"])
        col2.metric("Total Views", stats["Total Views"])
        col3.metric("Total Videos", stats["Total Videos"])
        col4.metric("Avg Views per Video", round(stats["Average Views per Video"]))
    
    topVideos = getTopVideos(channelID)
    
    if topVideos:
        st.subheader("🎬 Top 100 Videos by Views")
        df_videos = pd.DataFrame(topVideos)
        st.dataframe(df_videos)
        
        # Bar Chart: Top Performing Videos by Views
        fig1 = px.bar(df_videos, x="Title", y="Views", title="Top Performing Videos", text="Views", color="Likes")
        fig1.update_traces(texttemplate='%{text}', textposition='outside')
        fig1.update_layout(autosize=True, width=None, height=1000)
        st.plotly_chart(fig1)
        
        # Bubble Chart: Views vs. Likes (Size = Comments)
        fig2 = px.scatter(df_videos, x="Views", y="Likes", size="Comments", title="Views vs. Likes (Bubble Size = Comments)", hover_data=["Title"])
        fig2.update_layout(autosize=True, width=None, height=1000)        
        st.plotly_chart(fig2)
        
        # Bar Chart: Video Duration vs. Views
        fig3 = px.bar(df_videos, x="Title", y="Views", title="Video Duration vs. Views", color="Duration (s)", text="Views")
        fig3.update_traces(texttemplate='%{text}', textposition='outside')
        fig3.update_layout(autosize=True, width=None, height=1000)
        st.plotly_chart(fig3)
        
        # Heatmap: Correlation between Views, Likes, Comments, and Duration
        dfCorr = df_videos[["Views", "Likes", "Comments", "Duration (s)"]].corr()
        fig4 = px.imshow(dfCorr, text_auto=True, title="🔥 Heatmap: Correlation between Video Stats")
        fig4.update_layout(autosize=True, width=None, height=1000)
        st.plotly_chart(fig4)
        
        