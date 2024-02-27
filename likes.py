import streamlit as st
import requests
import pandas as pd
import numpy as np

url = "https://api.yodayo.com/v1/notifications"
limit = 500

user_likes = {}
user_comments = {}

# Allow users to input their own access token and session UUID
access_token = st.text_input("Enter your access token")

if access_token:
    session = requests.Session()
    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    session.cookies = jar

    def load_data():
        offset = 0
        while True:
            resp = session.get(url, params={"offset": offset, "limit": limit})
            data = resp.json()

            for notification in data.get("notifications", []):
                if notification["action"] == "liked":
                    name = notification["user_profile"]["name"]
                    resource_uuid = notification["resource_uuid"]

                    # Keep track of unique combinations of user and resource UUID for likes
                    unique_key = (name, resource_uuid)
                    if unique_key not in user_likes:
                        user_likes[unique_key] = 0

                    user_likes[unique_key] += 1

                if notification["action"] == "commented":
                    name = notification["user_profile"]["name"]
                    resource_uuid = notification["resource_uuid"]

                    if (name, resource_uuid) not in user_comments:
                        user_comments[(name, resource_uuid)] = 0

                    user_comments[(name, resource_uuid)] += 1

            if len(data.get("notifications", [])) < limit:
                break

            offset += limit

    if st.button("Load Data"):
        load_data()

        # Convert dictionaries to pandas dataframes
        df_likes = pd.DataFrame(list(user_likes.items()), columns=['User_Resource', 'Likes'])
        df_comments = pd.DataFrame(list(user_comments.items()), columns=['User_Resource', 'Comments'])

        # Split User_Resource column into User and Resource_UUID columns
        df_likes[['User', 'Resource_UUID']] = pd.DataFrame(df_likes['User_Resource'].tolist(), index=df_likes.index)
        df_comments[['User', 'Resource_UUID']] = pd.DataFrame(df_comments['User_Resource'].tolist(), index=df_comments.index)

        total_likes = df_likes['Likes'].sum()
        total_comments = df_comments['Comments'].sum()

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        # Display top liked and commented posts
        st.subheader("Top Liked Posts")
        st.table(df_likes.sort_values(by='Likes', ascending=False).head(5)[['User', 'Resource_UUID', 'Likes']])

        st.subheader("Top Commented Posts")
        st.table(df_comments.sort_values(by='Comments', ascending=False).head(5)[['User', 'Resource_UUID', 'Comments']])

        # Calculate and display average likes per user
        average_likes_per_user = total_likes / len(df_likes)
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        # User Percentile Analysis
        st.subheader("User Percentile Analysis")

        # Calculate percentiles
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values_likes = np.percentile(df_likes['Likes'], percentiles)
        percentiles_values_comments = np.percentile(df_comments['Comments'], percentiles)

        for percentile, value in zip(percentiles, percentiles_values_likes):
            st.write(f"{percentile}th percentile Likes: {value}")

        for percentile, value in zip(percentiles, percentiles_values_comments):
            st.write(f"{percentile}th percentile Comments: {value}")

else:
    st.warning("Please enter your access token and session UUID")
