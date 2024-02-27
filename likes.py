import streamlit as st
import requests

st.title("User Stats")

access_token = st.text_input("Enter access token") 
session_uuid = st.text_input("Enter session UUID")

url = "https://api.yodayo.com/v1/notifications"
limit = 500

user_likes = {}
user_comments = {}  

if access_token and session_uuid:

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

            # Access notifications list
            for notification in data["notifications"]:
                
                if notification["action"] == "liked":
                    name = notification["user_profile"]["name"]
                    if name not in user_likes: 
                        user_likes[name] = 0
                    user_likes[name] += 1
                        
                if notification["action"] == "commented":
                    # Tally comments
                    
            
            if len(data["notifications"]) < limit:
                break
                
            offset += limit
            
     
    if st.button("Load Data"): 
        load_data()
        
        # Display results..
        
else:
   st.warning("Enter access token and session UUID")
   
st.write("Data will load after clicking button")
