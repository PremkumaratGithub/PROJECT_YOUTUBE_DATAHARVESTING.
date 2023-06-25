# ==================================================       /     IMPORT LIBRARIES    /      =================================================== #
# YOUTUBE API LIBRARIES:-
import googleapiclient.discovery
from googleapiclient.discovery import build

# FILE HANDLING LIBRARIES:-
import json
import re

# MONGODB:-
import pymongo

# SQL LIBRARIES:-
import mysql.connector
import sqlalchemy
from sqlalchemy import create_engine
import pymysql

# PANDAS , NUMPY AND DASH BOARD LIBRARIES:-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ==============================================         /   /   DASHBOARD SETUP   /   /         ================================================== #

# CONFIGURING THE STREAMLIT GUI AND TITTLE SETUP:-
st.set_page_config(layout='wide')
st.title(':blue[YOUTUBE DATA HARVESTING AND WAREHOUSING]')

# ========================================   /     DATA COLLECTION AREA AND STORING THE DATA INTO MONGODB    /   =================================== #

# DATA COLLECTION AREA
col1, col2 = st.columns(2)
with col1:
    st.header(':red[DATA COLLECTION AREA]')
    st.write ('(Note:- In this area  **collecting the  data** from the **user** and stored it into the **:blue[MongoDB] database**.)')
    channel_id = st.text_input('**Enter the channel_id**')
    st.write('''Getting the  data from the user and stored it into the **MongoDB database** to click below **:blue['Getting data from user and stored']**.''')
    Get_data = st.button('**Getting data and stored**')

    # DEFINE SESSION STATE TO GET DATA BUTTON:-
    if "Get_state" not in st.session_state:
        st.session_state.Get_state = False
    if Get_data or st.session_state.Get_state:
        st.session_state.Get_state = True

        # FOR ACCESS YOUTUBE API:-
        api_service_name = 'youtube'
        api_version = 'v3'
        api_key = 'AIzaSyAgtSBIoTd_aNAzeGJnuBS2fhFTawwT1-k'
        youtube = build(api_service_name,api_version,developerKey =api_key)

        # ------------------------------------------------------#-------------------------------------------------------------------------#

        # DEFINE A FUNCTION TO RETRIVE THE CHANNEL DATA:-
        def get_channel_data(youtube,channel_id):
            try:
                try:
                    channel_request = youtube.channels().list( part = 'snippet,statistics,contentDetails',
                        id = channel_id)
                    channel_response = channel_request.execute()
                    
                    if 'items' not in channel_response:
                        st.write(f"Invalid channel id: {channel_id}")
                        st.error("Enter the correct 11-digit **channel_id**")
                        return None
                    
                    return channel_response
                
                except HttpError as e:
                    st.error('Server error (or) Check your internet connection (or) Please Try again after a few minutes', icon='🚨')
                    st.write('An error occurred: %s' % e)
                    return None
            except:
                st.write('You have exceeded your YouTube API quota, Please try again later.')

        # FUNCTION CALL TO GET THE CHANNEL DATA FROM A SINGLE CHANNEL ID:- 
        channel_data = get_channel_data(youtube,channel_id)

        # PROESS THE CHANNEL DATA:-
        # EXTRACT THE REQUIRED INFORMATION FROM THE CHANNEL DATA:-
        channel_name = channel_data['items'][0]['snippet']['title']
        channel_video_count = channel_data['items'][0]['statistics']['videoCount']
        channel_subscriber_count = channel_data['items'][0]['statistics']['subscriberCount']
        channel_view_count = channel_data['items'][0]['statistics']['viewCount']
        channel_description = channel_data['items'][0]['snippet']['description']
        channel_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # CONVERT THE CHANNEL DATA INTO DICTIONARY FORMAT:-
        channel = {
            "Channel_Details": {
                "Channel_Name": channel_name,
                "Channel_Id": channel_id,
                "Video_Count": channel_video_count,
                "Subscriber_Count": channel_subscriber_count,
                "Channel_Views": channel_view_count,
                "Channel_Description": channel_description,
                "Playlist_Id": channel_playlist_id
            }
        }

        # -------------------------------------------------------------------------------------------- #
        
        # DEFINE A FUNCTION TO RETRIEVE THE VIDEO ID'S FROM THE CHANNEL PLAYLIST.
        def get_video_ids(youtube, channel_playlist_id):
            
            video_id = []
            next_page_token = None
            while True:
                # GET THE PLAYLIST ITEMS:-
                request = youtube.playlistItems().list(part='contentDetails',playlistId=channel_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token)
                response = request.execute()

                # GET THE VIDEO:-
                for item in response['items']:
                    video_id.append(item['contentDetails']['videoId'])

                # TO CHECK IF THERE IS AN MORE PAGES:-
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return video_id

        # FUNCTION CALL TO GET TEHE VIDEO ID'S BY USING CHANNEL PLAYLIST ID:-
        video_ids = get_video_ids(youtube, channel_playlist_id)
        # -------------------------------------------------------------------------------------------- #

        # DEFINE A FUNCTION TO RETRIVE THE VIDEO DATA:- 
        def get_video_data(youtube, video_ids):
            
            video_data = []
            for video_id in video_ids:
                try:
                    # GET THE VIDEO DEATAILS:-
                    request = youtube.videos().list(
                        part='snippet, statistics, contentDetails',
                        id=video_id)
                    response = request.execute()

                    video = response['items'][0]
                    
                    # GET THE COMMENTS IF IT IS AVAILABLE (COMMENT FUCTION CALL)
                    try:
                        video['comment_threads'] = get_video_comments(youtube, video_id, max_comments=2)
                    except:
                        video['comment_threads'] = None

                    # DURATION FORMAT TRANSFORMATION (DURATION FORMAT TRANSFORMATION FUNCTION CALL)
                    duration = video.get('contentDetails', {}).get('duration', 'Not Available')
                    if duration != 'Not Available':
                        duration = convert_duration(duration)
                    video['contentDetails']['duration'] = duration        
                                
                    video_data.append(video)
                    
                except:
                    st.write('You have exceeded your YouTube API quota. Please try again later.')

            return video_data

        # DEFINE A FUNCTION TO RETRIVE THE VIDEO COMMENTS:-
        def get_video_comments(youtube, video_id, max_comments):
            
            request = youtube.commentThreads().list(part='snippet',maxResults=max_comments,textFormat="plainText",videoId=video_id)
            response = request.execute()
            return response

        # DEFINE A FUNCTION TO CONVERT THE VIDEO DURATION:-
        def convert_duration(duration):
            regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
            match = re.match(regex, duration)
            if not match:
                return '00:00:00'
            hours, minutes, seconds = match.groups()
            hours = int(hours[:-1]) if hours else 0
            minutes = int(minutes[:-1]) if minutes else 0
            seconds = int(seconds[:-1]) if seconds else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return '{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60), int(total_seconds % 60))

        # FUNCTION CALL TO GET THE VIDEOS DATA AND COMMENTS DATA FROM THE VIDEO ID'S:-
        video_data = get_video_data(youtube, video_ids)


        # PROCESSING THE VIDEO DETAILS:-
        videos = {}
        for i, video in enumerate (video_data):
            video_id = video['id']
            video_name = video['snippet']['title']
            video_description = video['snippet']['description']
            tags = video['snippet'].get('tags', [])
            published_at = video['snippet']['publishedAt']
            view_count = video['statistics']['viewCount']
            like_count = video['statistics'].get('likeCount', 0)
            dislike_count = video['statistics'].get('dislikeCount', 0)
            favorite_count = video['statistics'].get('favoriteCount', 0)
            comment_count = video['statistics'].get('commentCount', 0)
            duration = video.get('contentDetails', {}).get('duration', 'Not Available')
            thumbnail = video['snippet']['thumbnails']['high']['url']
            caption_status = video.get('contentDetails', {}).get('caption', 'Not Available')
            comments = 'Unavailable'

            # HANDLE CASE WHERE COMMENTS ARE ENABLED:-
            if video['comment_threads'] is not None:
                comments = {}
                for index, comment_thread in enumerate(video['comment_threads']['items']):
                    comment = comment_thread['snippet']['topLevelComment']['snippet']
                    comment_id = comment_thread['id']
                    comment_text = comment['textDisplay']
                    comment_author = comment['authorDisplayName']
                    comment_published_at = comment['publishedAt']
                    comments[f"Comment_Id_{index + 1}"] = {
                        'Comment_Id': comment_id,
                        'Comment_Text': comment_text,
                        'Comment_Author': comment_author,
                        'Comment_PublishedAt': comment_published_at
                    }
                    
            # CONVERT PROCESSED VIDEO DATA INTO DICSTIONARY FORMAT:-       
            videos[f"Video_Id_{i + 1}"] = {
                'Video_Id': video_id,
                'Video_Name': video_name,
                'Video_Description': video_description,
                'Tags': tags,
                'PublishedAt': published_at,
                'View_Count': view_count,
                'Like_Count': like_count,
                'Dislike_Count': dislike_count,
                'Favorite_Count': favorite_count,
                'Comment_Count': comment_count,
                'Duration': duration,
                'Thumbnail': thumbnail,
                'Caption_Status': caption_status,
                'Comments': comments
            }

        # ---------------------------------------------------------------------------------------------------------------------------#

        #COMBINE THE CHANNEL DATA AND THE VIDEOS DATA INTO THE DICSTIONARY:- 
        final_output = {**channel, **videos}

        # ---------------------------------------------------------------------------------------------------------------------------#

        # -----------------------------------    /   MONGODB CONNECTION AND STORE THE COLLECTED DATA   /    ---------------------------------- #

        # CREATE A CLINENT INSTANCE OF MONGODB:-
        client = pymongo.MongoClient('mongodb://localhost:27017')

        # CREATE A DATABASE OR USE EXITING ONE:-
        mydb = client['Youtube_DB']

        # CREATE A COLLECTION:-
        collection = mydb['Youtube_data']

        # DEFINE THE DATA TO INSERT:-
        final_output_data = {
            'Channel_Name': channel_name,
            "Channel_data":final_output
            }

        # INSERT OR UPDATE THE DATA IN THE COLLECTION:-
        upload = collection.replace_one({'_id': channel_id}, final_output_data, upsert=True)

        # PRINT THE RESULT OF THE INSERTION OPERATION:-
        st.write(f"Updated document id: {upload.upserted_id if upload.upserted_id else upload.modified_count}")

        # CLOSE THE CONNECTION:-
        client.close()

# ========================================   /     DATA TRANSFER AREA (STORED DATA TO MYSQL)    /   ========================================== #

with col2:
    st.header(':red[DATA TRANSFER AREA]')
    st.write ('''(Note:- In this area specific channel data **transfer to :blue[MySQL] database from  :blue[MongoDB] database** depend upon your selection,
                if it is unavailable then you have to collect data first.)''')
    
     # CONNECTING THE MONGODB SERVER:-
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # CREATE A DATABASE OR USE THE EXCISTING ONE:-
    mydb = client['Youtube_DB']

    # CREATE A COLLECTION:-
    collection = mydb['Youtube_data']

    # COLLECT ALL THE DOCUMENT NAMES AND GIVEN THEM:-
    document_names = []
    for document in collection.find():
        document_names.append(document["Channel_Name"])
    document_name = st.selectbox('**Select Channel name**', options = document_names, key='document_names')
    st.write('''transfer to MySQL database from MongoDB database to click below **:blue['transfer to MySQL']**.''')
    Migrate = st.button('**transfer to MySQL**')
    
     # DEFINE SESSION STATE TO TRANSFER TO MSQL BUTTON:-
    if 'transfer_sql' not in st.session_state:
        st.session_state_transfer_sql = False
    if Migrate or st.session_state_transfer_sql:
        st.session_state_transfer_sql = True

        # RETRIVE THE DOCUMENT WITH THE SPECIFIED NAME:-
        result = collection.find_one({"Channel_Name": document_name})
        client.close()

        # ---------------------------------------------- DATA CONVERSION----------------------------------------- #

        # CONVERT THE CHANNEL DATA JSON TO DF:-
        channel_details_to_sql = {
            "Channel_Name": result['Channel_Name'],
            "Channel_Id": result['_id'],
            "Video_Count": result['Channel_data']['Channel_Details']['Video_Count'],
            "Subscriber_Count": result['Channel_data']['Channel_Details']['Subscriber_Count'],
            "Channel_Views": result['Channel_data']['Channel_Details']['Channel_Views'],
            "Channel_Description": result['Channel_data']['Channel_Details']['Channel_Description'],
            "Playlist_Id": result['Channel_data']['Channel_Details']['Playlist_Id']
            }
        channel_df = pd.DataFrame.from_dict(channel_details_to_sql, orient='index').T
              
        # CONVERT THE PLAYLIST DATA JSON TO DF:-
        playlist_tosql = {"Channel_Id": result['_id'],
                        "Playlist_Id": result['Channel_data']['Channel_Details']['Playlist_Id']
                        }
        playlist_df = pd.DataFrame.from_dict(playlist_tosql, orient='index').T

        # CONVERT THE VIDEO DATA JSON TO DF:-
        video_details_list = []
        for i in range(1,len(result['Channel_data'])-1):
            video_details_tosql = {
                'Playlist_Id':result['Channel_data']['Channel_Details']['Playlist_Id'],
                'Video_Id': result['Channel_data'][f"Video_Id_{i}"]['Video_Id'],
                'Video_Name': result['Channel_data'][f"Video_Id_{i}"]['Video_Name'],
                'Video_Description': result['Channel_data'][f"Video_Id_{i}"]['Video_Description'],
                'Published_date': result['Channel_data'][f"Video_Id_{i}"]['PublishedAt'],
                'View_Count': result['Channel_data'][f"Video_Id_{i}"]['View_Count'],
                'Like_Count': result['Channel_data'][f"Video_Id_{i}"]['Like_Count'],
                'Dislike_Count': result['Channel_data'][f"Video_Id_{i}"]['Dislike_Count'],
                'Favorite_Count': result['Channel_data'][f"Video_Id_{i}"]['Favorite_Count'],
                'Comment_Count': result['Channel_data'][f"Video_Id_{i}"]['Comment_Count'],
                'Duration': result['Channel_data'][f"Video_Id_{i}"]['Duration'],
                'Thumbnail': result['Channel_data'][f"Video_Id_{i}"]['Thumbnail'],
                'Caption_Status': result['Channel_data'][f"Video_Id_{i}"]['Caption_Status']
                }
            video_details_list.append(video_details_tosql)
        video_df = pd.DataFrame(video_details_list)

        # CONVERT THE COMMENT DATA JSON TO DF:-
        Comment_details_list = []
        for i in range(1, len(result['Channel_data']) - 1):
            comments_access = result['Channel_data'][f"Video_Id_{i}"]['Comments']
            if comments_access == 'Unavailable' or ('Comment_Id_1' not in comments_access or 'Comment_Id_2' not in comments_access) :
                Comment_details_tosql = {
                    'Video_Id': 'Unavailable',
                    'Comment_Id': 'Unavailable',
                    'Comment_Text': 'Unavailable',
                    'Comment_Author':'Unavailable',
                    'Comment_Published_date': 'Unavailable',
                    }
                Comment_details_list.append(Comment_details_tosql)
                
            else:
                for j in range(1,3):
                    Comment_details_tosql = {
                    'Video_Id': result['Channel_data'][f"Video_Id_{i}"]['Video_Id'],
                    'Comment_Id': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Id'],
                    'Comment_Text': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Text'],
                    'Comment_Author': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_Author'],
                    'Comment_Published_date': result['Channel_data'][f"Video_Id_{i}"]['Comments'][f"Comment_Id_{j}"]['Comment_PublishedAt'],
                    }
                    Comment_details_list.append(Comment_details_tosql)
        Comments_df = pd.DataFrame(Comment_details_list)

        # -------------------------------------------DATA TRANSFERED TO MYSQL ----------------------------------------- #

        # CONNECT THE MSQL SERVER:-
        connect = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "root",
        auth_plugin = "mysql_native_password")

        # CREATE AND USE THE NEW DATABASE:-
        mycursor = connect.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS youtube_db")

        # CLOSE THE CORSOR AND DATABASE CONNECTION:-
        mycursor.close()
        connect.close()

        # CONNECT TO THE NEW CREATED DATABASE:-
        engine = create_engine('mysql+mysqlconnector://root:root@localhost/youtube_db', echo=False)

        # USE PANDAS TO INSERT THE DATAFRAMES DATA TO THE SQL DATABASE -> TABLE1

        # CHANNEL DATA TO SQL:-
        channel_df.to_sql('channel', engine, if_exists='append', index=False,
                        dtype = {"Channel_Name": sqlalchemy.types.VARCHAR(length=225),
                                "Channel_Id": sqlalchemy.types.VARCHAR(length=225),
                                "Video_Count": sqlalchemy.types.INT,
                                "Subscriber_Count": sqlalchemy.types.BigInteger,
                                "Channel_Views": sqlalchemy.types.BigInteger,
                                "Channel_Description": sqlalchemy.types.TEXT,
                                "Playlist_Id": sqlalchemy.types.VARCHAR(length=225),})

        # PLAYLIST DATA TO SQL:-
        playlist_df.to_sql('playlist', engine, if_exists='append', index=False,
                        dtype = {"Channel_Id": sqlalchemy.types.VARCHAR(length=225),
                                    "Playlist_Id": sqlalchemy.types.VARCHAR(length=225),})

        #VIDEO DATA TO SQL:-
        video_df.to_sql('video', engine, if_exists='append', index=False,
                    dtype = {'Playlist_Id': sqlalchemy.types.VARCHAR(length=225),
                            'Video_Id': sqlalchemy.types.VARCHAR(length=225),
                            'Video_Name': sqlalchemy.types.VARCHAR(length=225),
                            'Video_Description': sqlalchemy.types.TEXT,
                            'Published_date': sqlalchemy.types.String(length=50),
                            'View_Count': sqlalchemy.types.BigInteger,
                            'Like_Count': sqlalchemy.types.BigInteger,
                            'Dislike_Count': sqlalchemy.types.INT,
                            'Favorite_Count': sqlalchemy.types.INT,
                            'Comment_Count': sqlalchemy.types.INT,
                            'Duration': sqlalchemy.types.VARCHAR(length=1024),
                            'Thumbnail': sqlalchemy.types.VARCHAR(length=225),
                            'Caption_Status': sqlalchemy.types.VARCHAR(length=225),})

        # COMMENT DATA TO SQL:-
        Comments_df.to_sql('comments', engine, if_exists='append', index=False,
                        dtype = {'Video_Id': sqlalchemy.types.VARCHAR(length=225),
                                'Comment_Id': sqlalchemy.types.VARCHAR(length=225),
                                'Comment_Text': sqlalchemy.types.TEXT,
                                'Comment_Author': sqlalchemy.types.VARCHAR(length=225),
                                'Comment_Published_date': sqlalchemy.types.String(length=50),})

# ====================================================   /     CHANNEL DATA ANALYSIS AREA     /   ================================================= #

st.header(':red[CHANNEL DATA ANALYSIS AREA]')
st.write ('''(Note:- In this area **Analysis of a collection of channel data** depend upon your question selection it gives the table format output.)''')

# CHECK AVAILABLE CHANNEL DATA:-
Check_channel = st.checkbox('**Check available channel data for analysis**')

if Check_channel:
   # CREATE A DATABSE CONNECTION:-
    engine = create_engine('mysql+mysqlconnector://root:root@localhost/youtube_db', echo=False)
    # EXECUTE SQL QUERY TO RETRIEVE CHANNEL NAMES:-
    query = "SELECT Channel_Name FROM channel;"
    results = pd.read_sql(query, engine)
    # GET CHANNEL NAMES AS A LIST:-
    channel_names_fromsql = list(results['Channel_Name'])
    # CREATE A DATA FRAME FROM THE LIST AND RESET THE INDEX TO START FROM 1:-
    df_at_sql = pd.DataFrame(channel_names_fromsql, columns=['Available channel data']).reset_index(drop=True)
    # RESET THE INDEX TO START FROM 1 INSTEAD OF 0:-
    df_at_sql.index += 1  
    # SHOW DATAFRAME:-
    st.dataframe(df_at_sql)

# -----------------------------------------------------     /   QUESTIONS   /    ------------------------------------------------------------- #
st.subheader(':violet[Channels Analysis ]')

# CREATING THE SELECTBOX:-
question_tosql = st.selectbox('**Select your Question**',
('1. What are the names of all the videos and their corresponding channels?',
'2. Which channels have the most number of videos, and how many videos do they have?',
'3. What are the top 10 most viewed videos and their respective channels?',
'4. How many comments were made on each video, and what are their corresponding video names?',
'5. Which videos have the highest number of likes, and what are their corresponding channel names?',
'6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
'7. What is the total number of views for each channel, and what are their corresponding channel names?',
'8. What are the names of all the channels that have published videos in the year 2022?',
'9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
'10. Which videos have the highest number of comments, and what are their corresponding channel names?'), key = 'collection_question')

# CREATE A CONNECTION TO SQL:-
connect_for_question = pymysql.connect(host='localhost', user='root', password='root', db='youtube_db')
cursor = connect_for_question.cursor()

# Q1
if question_tosql == '1. What are the names of all the videos and their corresponding channels?':
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name FROM channel JOIN playlist JOIN video ON channel.Channel_Id = playlist.Channel_Id AND playlist.Playlist_Id = video.Playlist_Id;")
    result_1 = cursor.fetchall()
    df1 = pd.DataFrame(result_1, columns=['Channel Name', 'Video Name']).reset_index(drop=True)
    df1.index += 1
    st.dataframe(df1)

# Q2
elif question_tosql == '2. Which channels have the most number of videos, and how many videos do they have?':

    col1,col2 = st.columns(2)
    with col1:
        cursor.execute("SELECT Channel_Name, Video_Count FROM channel ORDER BY Video_Count DESC;")
        result_2 = cursor.fetchall()
        df2 = pd.DataFrame(result_2,columns=['Channel Name','Video Count']).reset_index(drop=True)
        df2.index += 1
        st.dataframe(df2)

    with col2:
        fig_vc = px.bar(df2, y='Video Count', x='Channel Name', text_auto='.2s', title="Most number of videos", )
        fig_vc.update_traces(textfont_size=16,marker_color='#E6064A')
        fig_vc.update_layout(title_font_color='#1308C2 ',title_font=dict(size=25))
        st.plotly_chart(fig_vc,use_container_width=True)

# Q3
elif question_tosql == '3. What are the top 10 most viewed videos and their respective channels?':

    col1,col2 = st.columns(2)
    with col1:
        cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.View_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.View_Count DESC LIMIT 10;")
        result_3 = cursor.fetchall()
        df3 = pd.DataFrame(result_3,columns=['Channel Name', 'Video Name', 'View count']).reset_index(drop=True)
        df3.index += 1
        st.dataframe(df3)

    with col2:
        fig_topvc = px.bar(df3, y='View count', x='Video Name', text_auto='.2s', title="Top 10 most viewed videos")
        fig_topvc.update_traces(textfont_size=16,marker_color='#E6064A')
        fig_topvc.update_layout(title_font_color='#1308C2 ',title_font=dict(size=25))
        st.plotly_chart(fig_topvc,use_container_width=True)

# Q4 
elif question_tosql == '4. How many comments were made on each video, and what are their corresponding video names?':
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Comment_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id;")
    result_4 = cursor.fetchall()
    df4 = pd.DataFrame(result_4,columns=['Channel Name', 'Video Name', 'Comment count']).reset_index(drop=True)
    df4.index += 1
    st.dataframe(df4)

# Q5
elif question_tosql == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Like_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Like_Count DESC;")
    result_5= cursor.fetchall()
    df5 = pd.DataFrame(result_5,columns=['Channel Name', 'Video Name', 'Like count']).reset_index(drop=True)
    df5.index += 1
    st.dataframe(df5)

# Q6
elif question_tosql == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
    st.write('**Note:- In November 2021, YouTube removed the public dislike count from all of its videos.**')
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Like_Count, video.Dislike_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Like_Count DESC;")
    result_6= cursor.fetchall()
    df6 = pd.DataFrame(result_6,columns=['Channel Name', 'Video Name', 'Like count','Dislike count']).reset_index(drop=True)
    df6.index += 1
    st.dataframe(df6)

# Q7
elif question_tosql == '7. What is the total number of views for each channel, and what are their corresponding channel names?':

    col1, col2 = st.columns(2)
    with col1:
        cursor.execute("SELECT Channel_Name, Channel_Views FROM channel ORDER BY Channel_Views DESC;")
        result_7= cursor.fetchall()
        df7 = pd.DataFrame(result_7,columns=['Channel Name', 'Total number of views']).reset_index(drop=True)
        df7.index += 1
        st.dataframe(df7)
    
    with col2:
        fig_topview = px.bar(df7, y='Total number of views', x='Channel Name', text_auto='.2s', title="Total number of views", )
        fig_topview.update_traces(textfont_size=16,marker_color='#E6064A')
        fig_topview.update_layout(title_font_color='#1308C2 ',title_font=dict(size=25))
        st.plotly_chart(fig_topview,use_container_width=True)

# Q8
elif question_tosql == '8. What are the names of all the channels that have published videos in the year 2022?':
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Published_date FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id  WHERE EXTRACT(YEAR FROM Published_date) = 2022;")
    result_8= cursor.fetchall()
    df8 = pd.DataFrame(result_8,columns=['Channel Name','Video Name', 'Year 2022 only']).reset_index(drop=True)
    df8.index += 1
    st.dataframe(df8)

# Q9
elif question_tosql == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
    cursor.execute("SELECT channel.Channel_Name, TIME_FORMAT(SEC_TO_TIME(AVG(TIME_TO_SEC(TIME(video.Duration)))), '%H:%i:%s') AS duration  FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id GROUP by Channel_Name ORDER BY duration DESC ;")
    result_9= cursor.fetchall()
    df9 = pd.DataFrame(result_9,columns=['Channel Name','Average duration of videos (HH:MM:SS)']).reset_index(drop=True)
    df9.index += 1
    st.dataframe(df9)

# Q10
elif question_tosql == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
    cursor.execute("SELECT channel.Channel_Name, video.Video_Name, video.Comment_Count FROM channel JOIN playlist ON channel.Channel_Id = playlist.Channel_Id JOIN video ON playlist.Playlist_Id = video.Playlist_Id ORDER BY video.Comment_Count DESC;")
    result_10= cursor.fetchall()
    df10 = pd.DataFrame(result_10,columns=['Channel Name','Video Name', 'Number of comments']).reset_index(drop=True)
    df10.index += 1
    st.dataframe(df10)

# CLOSE THE SQL DATABASE CONNECION:-
connect_for_question.close()
# ==================================================================#===================================================================#
