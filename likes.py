import streamlit as st
import requests 
import json

st.title("User Likes")

url = "https://api.yodayo.com/v1/notifications"  

offset = 0
limit = 500

user_likes = {}

def load_data():
    while True:
        params = {"offset": offset, "limit": limit}
        resp = requests.get(url, params=params)
        data = json.loads(resp.text)    

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
    
    for name, likes in user_likes.items():
        st.write(f"{name}: {likes}")
        
st.write("Data will be loaded after clicking button")