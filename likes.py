import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
from io import BytesIO
import gzip

url = "https://api.yodayo.com/v1/notifications"
limit = 500

# Allow users to input their own access token
access_token = st.text_input("Enter your access token")

if access_token:
    session = requests.Session()
    headers = {
        "Accept-Encoding": "gzip, deflate",
    }
    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    session.cookies = jar

    def load_data():
        offset = 0
        notifications = []
        while True:
            resp = session.get(url, params={"offset": offset, "limit": limit}, headers=headers)
            data = resp.content

            # Decompress gzip data
            with gzip.GzipFile(fileobj=BytesIO(data), mode='rb') as f:
                decoded_data = f.read()
                decoded_json = json.loads(decoded_data)

            notifications.extend(decoded_json.get("notifications", []))

            if len(decoded_json.get("notifications", [])) < limit:
                break

            offset += limit

        return notifications

    notifications_data = load_data()

    # Create pandas DataFrames for likes and comments
    likes_df = pd.DataFrame(columns=["User", "Likes"])
    comments_df = pd.DataFrame(columns=["User", "Comments"])

    for notification in notifications_data:
        user_name = notification["user_profile"]["name"]
        action = notification["action"]

        if action == "liked":
            likes_df = likes_df.append({"User": user_name, "Likes": 1}, ignore_index=True)
        elif action == "commented":
            comments_df = comments_df.append({"User": user_name, "Comments": 1}, ignore_index=True)

    if st.button("Load Data"):
        st.subheader("Likes DataFrame")
        st.write(likes_df.groupby("User").size().sort_values(ascending=False).reset_index(name="Likes"))

        st.subheader("Comments DataFrame")
        st.write(comments_df.groupby("User").size().sort_values(ascending=False).reset_index(name="Comments"))

        total_likes = likes_df["Likes"].sum()
        total_comments = comments_df["Comments"].sum()

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        # Display top liked and commented posts
        st.subheader("Top Liked Posts")
        top_liked_posts = likes_df.groupby("User")["Likes"].sum().sort_values(ascending=False).head(5).reset_index()
        st.write(top_liked_posts)

        st.subheader("Top Commented Posts")
        top_commented_posts = comments_df.groupby("User")["Comments"].sum().sort_values(ascending=False).head(5).reset_index()
        st.write(top_commented_posts)

        # Calculate and display average likes per user
        average_likes_per_user = total_likes / len(likes_df["User"].unique())
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        # User Percentile Analysis
        st.subheader("User Percentile Analysis")

        # Calculate percentiles
        likes_per_user = likes_df.groupby("User")["Likes"].sum()
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values = np.percentile(likes_per_user, percentiles)

        for percentile, value in zip(percentiles, percentiles_values):
            st.write(f"{percentile}th percentile: {value} likes")

else:
    st.warning("Please enter your access token")
