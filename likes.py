import streamlit as st
import requests

st.title("User Likes")

url = "https://api.yodayo.com/v1/notifications"  

limit = 500

user_likes = {}

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
        params = {"offset": offset, "limit": limit}
        resp = session.get(url, params=params)
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
    
    st.subheader("User Likes")
    for name, likes in user_likes.items():
        st.write(f"{name}: {likes}")
        
st.write("Data will be loaded after clicking button")
