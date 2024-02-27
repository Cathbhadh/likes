import streamlit as st
import requests
import numpy as np

url = "https://api.yodayo.com/v1/notifications"
limit = 500

user_likes = {}
user_comments = {}

# Allow users to input their own access token and session UUID
access_token = st.text_input("Enter your access token")
session_uuid = st.text_input("Enter your session UUID")

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

            for notification in data.get("notifications", []):
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

            if len(data.get("notifications", [])) < limit:
                break

            offset += limit

    if st.button("Load Data"):
        load_data()

        total_likes = sum(user_likes.values())
        total_comments = sum(user_comments.values())

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        # Display top liked and commented posts
        st.subheader("Top Liked Posts")
        top_liked_posts = sorted(user_likes.items(), key=lambda x: x[1], reverse=True)[:5]
        for name, likes in top_liked_posts:
            st.write(f"{name}: {likes} likes")

        st.subheader("Top Commented Posts")
        top_commented_posts = sorted(user_comments.items(), key=lambda x: x[1], reverse=True)[:5]
        for name, comments in top_commented_posts:
            st.write(f"{name}: {comments} comments")

        # Calculate and display average likes per user
        average_likes_per_user = total_likes / len(user_likes)
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        # User Percentile Analysis
        st.subheader("User Percentile Analysis")

        # Calculate percentiles
        likes_per_user = list(user_likes.values())
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values = np.percentile(likes_per_user, percentiles)

        for percentile, value in zip(percentiles, percentiles_values):
            st.write(f"{percentile}th percentile: {value} likes")

else:
    st.warning("Please enter your access token and session UUID")
