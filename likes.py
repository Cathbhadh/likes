import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

API_URL = "https://api.yodayo.com/v1/notifications"
LIMIT = 500


def authenticate_with_token(access_token):
    session = requests.Session()
    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    session.cookies = jar
    return session


def process_liked_notification(notification, user_likes):
    name = notification["user_profile"]["name"]
    resource_uuid = notification["resource_uuid"]

    user_likes.setdefault(name, set()).add(resource_uuid)


def load_data(session):
    offset = 0
    user_likes = {}

    while True:
        resp = session.get(API_URL, params={"offset": offset, "limit": LIMIT})
        data = resp.json()

        for notification in data.get("notifications", []):
            if notification["action"] == "liked" and notification.get("resource_media"):
                process_liked_notification(notification, user_likes)

        if len(data.get("notifications", [])) < LIMIT:
            break

        offset += LIMIT

    return user_likes


def display_top_users_stats(likes_df, percentile, total_likes):
    top_users = likes_df.sort_values("Likes", ascending=False).head(
        int(percentile * len(likes_df))
    )
    pct_top_users = len(top_users) / len(likes_df) * 100
    pct_likes_top_users = top_users["Likes"].sum() / total_likes * 100
    st.write(
        f"{len(top_users)} users ({pct_top_users:.1f}% of all users) contributed {pct_likes_top_users:.1f}% of total likes"
    )


def main():
    access_token = st.text_input("Enter your access token")

    if access_token:
        session = authenticate_with_token(access_token)

        if st.button("Load Data"):
            user_likes = load_data(session)

            # Create a DataFrame from user_likes
            liked_posts_data = []

            for user, liked_posts in user_likes.items():
                for post_uuid in liked_posts:
                    liked_posts_data.append({"User": user, "Post_UUID": post_uuid})

            likes_df = pd.DataFrame(liked_posts_data)

            st.subheader("Likes by user:")
            st.dataframe(likes_df)

            total_likes = len(liked_posts_data)

            st.subheader("Total Likes")
            st.write(f"Total Likes: {total_likes}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Likes by user:")
                st.dataframe(likes_df)

            with col2:
                st.subheader("Likes Percentiles")
                percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                percentiles_values_likes = np.percentile(likes_df["Likes"], percentiles)

                for percentile, value in zip(percentiles, percentiles_values_likes):
                    rounded_value = round(value, 2)
                    st.write(f"{percentile}th percentile: {rounded_value}")

            st.subheader("% of Likes by Top Users")
            display_top_users_stats(likes_df, 0.10, total_likes)
            display_top_users_stats(likes_df, 0.25, total_likes)
            display_top_users_stats(likes_df, 0.50, total_likes)

    else:
        st.warning("Enter your access token:")


if __name__ == "__main__":
    main()
