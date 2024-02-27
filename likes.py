import streamlit as st
import requests
import pandas as pd
import numpy as np

API_URL = "https://api.yodayo.com/v1/notifications"
LIMIT = 500

def authenticate_with_token(access_token):
    session = requests.Session()
    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    session.cookies = jar
    return session

def process_liked_notification(notification, user_likes_df):
    name = notification["user_profile"]["name"]
    resource_uuid = notification["resource_uuid"]

    user_likes_df = pd.concat([user_likes_df, pd.DataFrame({"User": [name], "Likes": [resource_uuid]})], ignore_index=True)
    return user_likes_df

def process_commented_notification(notification, user_comments_df):
    name = notification["user_profile"]["name"]

    user_comments_df.loc[name] = user_comments_df.get(name, 0) + 1
    return user_comments_df

def load_data(session):
    offset = 0
    user_likes_df = pd.DataFrame(columns=["User", "Likes"])
    user_comments_df = pd.DataFrame(columns=["User", "Comments"])

    while True:
        resp = session.get(API_URL, params={"offset": offset, "limit": LIMIT})
        data = resp.json()

        for notification in data.get("notifications", []):
            if notification["action"] == "liked" and notification.get("resource_media"):
                user_likes_df = process_liked_notification(notification, user_likes_df)

            if notification["action"] == "commented":
                user_comments_df = process_commented_notification(notification, user_comments_df)

        if len(data.get("notifications", [])) < LIMIT:
            break

        offset += LIMIT

    return user_likes_df, user_comments_df

def main():
    access_token = st.text_input("Enter your access token")

    if access_token:
        session = authenticate_with_token(access_token)

        if st.button("Load Data"):
            user_likes_df, user_comments_df = load_data(session)

            total_likes = user_likes_df.groupby("User")["Likes"].nunique().sum()
            total_comments = user_comments_df["Comments"].sum()

            st.subheader("Total Likes and Comments")
            st.write(f"Total Likes: {total_likes}")
            st.write(f"Total Comments: {total_comments}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Likes by user:")
                st.dataframe(user_likes_df["User"].value_counts().reset_index().rename(columns={"index": "User", "User": "Likes"}))

            with col2:
                st.subheader("Comments by user:")
                st.dataframe(user_comments_df)

            average_likes_per_user = total_likes / len(user_likes_df["User"].unique())
            st.subheader("Average Likes per User")
            st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

            st.subheader("Percentile:")
            percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            percentiles_values_likes = np.percentile(user_likes_df.groupby("User")["Likes"].nunique(), percentiles)
            percentiles_values_comments = np.percentile(user_comments_df["Comments"], percentiles)

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

if __name__ == "__main__":
    main()
