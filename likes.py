import streamlit as st
import requests
import pandas as pd
import numpy as np

url = "https://api.yodayo.com/v1/notifications"
limit = 500

user_likes = {}
user_comments = {}

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
                    post_id = notification["post"]["id"]

                    if name not in user_likes:
                        user_likes[name] = set()

                    user_likes[name].add(post_id)

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

        # Count the number of unique liked posts for each user
        likes_counts = {name: len(posts) for name, posts in user_likes.items()}
        df_likes = pd.DataFrame(list(likes_counts.items()), columns=["User", "Likes"])

        df_comments = pd.DataFrame(
            list(user_comments.items()), columns=["User", "Comments"]
        )

        total_likes = df_likes["Likes"].sum()
        total_comments = df_comments["Comments"].sum()

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Likes by user:")
            st.dataframe(df_likes.sort_values(by="Likes", ascending=False))

        with col2:
            st.subheader("Comments by user:")
            st.dataframe(df_comments.sort_values(by="Comments", ascending=False))

        average_likes_per_user = total_likes / len(df_likes)
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        st.subheader("Percentile:")
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values_likes = np.percentile(df_likes['Likes'], percentiles)
        percentiles_values_comments = np.percentile(df_comments['Comments'], percentiles)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Likes Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_likes):
                st.write(f"{percentile}th percentile: {value}")

        with col2:
            st.subheader("Comments Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_comments):
                st.write(f"{percentile}th percentile: {value}")

else:
    st.warning("Please enter your access token")
