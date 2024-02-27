import streamlit as st
import requests
import pandas as pd
import numpy as np

url = "https://api.yodayo.com/v1/notifications"
limit = 500

# Allow users to input their own access token and session UUID
access_token = st.text_input("Enter your access token")

if access_token:
    session = requests.Session()
    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    session.cookies = jar

    def load_data():
        data_list = []
        offset = 0
        while True:
            resp = session.get(url, params={"offset": offset, "limit": limit})
            data = resp.json()

            for notification in data.get("notifications", []):
                user_profile = notification["user_profile"]
                resource_uuid = notification["resource_uuid"]
                action = notification["action"]

                data_list.append({"User": user_profile["name"], "Resource_UUID": resource_uuid, "Action": action})

            if len(data.get("notifications", [])) < limit:
                break

            offset += limit

        return pd.DataFrame(data_list)

    if st.button("Load Data"):
        df_notifications = load_data()

        # Count occurrences of each combination of User, Resource_UUID, and Action
        df_counts = df_notifications.groupby(['User', 'Resource_UUID', 'Action']).size().reset_index(name='Count')

        # Separate likes and comments
        df_likes = df_counts[df_counts['Action'] == 'liked']
        df_comments = df_counts[df_counts['Action'] == 'commented']

        total_likes = len(df_likes)
        total_comments = len(df_comments)

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        # Display top liked and commented posts
        st.subheader("Top Liked Posts")
        st.table(df_likes.sort_values(by='Count', ascending=False))

        st.subheader("Top Commented Posts")
        st.table(df_comments.sort_values(by='Count', ascending=False))

        # Calculate and display average likes per user
        average_likes_per_user = total_likes / len(df_likes['User'].unique())
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        # User Percentile Analysis
        st.subheader("User Percentile Analysis")

        # Calculate percentiles
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values_likes = np.percentile(df_likes['Count'], percentiles)

        for percentile, value in zip(percentiles, percentiles_values_likes):
            st.write(f"{percentile}th percentile Likes: {value}")

else:
    st.warning("Please enter your access token and session UUID")
