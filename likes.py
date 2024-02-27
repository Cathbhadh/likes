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
                    # Tally likes
                
                if notification["action"] == "commented":
                    # Tally comments
           
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
            
else:
    st.warning("Please enter access token and session UUID")
    
st.write("Data will load after clicking button")
