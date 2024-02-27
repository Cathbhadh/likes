import streamlit as st
import requests

# Authentication code

url = "https://api.yodayo.com/v1/notifications"

limit = 500
user_likes = {}

def load_data():
    offset = 0
    
    while True:
        params = {"offset": offset, "limit": limit}  
        resp = session.get(url, params=params)
        data = resp.json()

        for notification in data["notifications"]:
            if notification["action"] == "liked":
                name = notification["user_profile"]["name"]  
                if name not in user_likes:
                    user_likes[name] = 0
                user_likes[name] += 1

        if len(data["notifications"]) < limit:            
            break
        
        offset += limit
        
if st.button("Load Data"):
    load_data()  
    
    # Sort user likes
    sorted_likes = sorted(user_likes.items(), key=lambda x: x[1], reverse=True)
    
    for name, likes in sorted_likes:
        st.write(f"{name}: {likes}")
