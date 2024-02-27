import streamlit as st
import requests

url = "https://api.yodayo.com/v1/notifications"  

limit = 500

user_likes = {} 
user_comments = {}
secrets = st.secrets["secrets"]
access_token = secrets["access_token"] 
session_uuid = secrets["session_uuid"]

session = requests.Session()
jar = requests.cookies.RequestsCookieJar()
jar.set("access_token", access_token)  
jar.set("session_uuid", session_uuid)
session.cookies = jar
def load_data():

    offset = 0
    
    while True:  
        resp = session.get(url, params={"offset": offset, "limit": limit})
        data = resp.json()

        for notification in data["notifications"]:
            if notification["action"] == "liked":
                name = notification["user_profile"]["name"]
                
                if name not in user_likes:
                    user_likes[name] = 0
                    
                user_likes[name] += 1
            
            if notification["action"] == "commented":
                name = notification["user_profile"]["name"]  
                
                if name not in user_comments:
                    user_comments[name] = 0
                    
                user_comments[name] += 1

        if len(data["notifications"]) < limit:
            break
        
        offset += limit
                  
if st.button("Load Data"):
    load_data()   
    
    sorted_likes = sorted(user_likes.items(), key=lambda x: x[1], reverse=True) 
    sorted_comments = sorted(user_comments.items(), key=lambda x: x[1], reverse=True)
    
    st.subheader("Likes")
    for name, likes in sorted_likes:
        st.write(f"{name}: {likes}")
        
    st.subheader("Comments")
    for name, comments in sorted_comments:
        st.write(f"{name}: {comments}")
