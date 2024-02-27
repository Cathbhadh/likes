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


def process_commented_notification(notification, user_comments, resource_comments):
    name = notification["user_profile"]["name"]
    resource_uuid = notification["resource_uuid"]

    user_comments[name] = user_comments.get(name, 0) + 1
    resource_comments[resource_uuid] = resource_comments.get(resource_uuid, 0) + 1


def load_data(session):
    offset = 0
    user_likes = {}
    user_comments = {}
    resource_comments = {}

    while True:
        resp = session.get(API_URL, params={"offset": offset, "limit": LIMIT})
        data = resp.json()

        for notification in data.get("notifications", []):
            if notification["action"] == "liked" and notification.get("resource_media"):
                process_liked_notification(notification, user_likes)

            if notification["action"] == "commented":
                process_commented_notification(notification, user_comments, resource_comments)

        if len(data.get("notifications", [])) < LIMIT:
            break

        offset += LIMIT

    return user_likes, user_comments, resource_comments


def main():
    access_token = st.text_input("Enter your access token")

    if access_token:
        session = authenticate_with_token(access_token)

        if st.button("Load Data"):
            start_time = time.perf_counter()
            user_likes, user_comments, resource_comments = load_data(session)

            total_likes = sum(len(posts) for posts in user_likes.values())
            total_comments = sum(user_comments.values())

            st.subheader("Total Likes and Comments")
            st.write(f"Total Likes: {total_likes}")
            st.write(f"Total Comments: {total_comments}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Likes by user:")
                likes_df = pd.DataFrame(
                    {
                        "User": list(user_likes.keys()),
                        "Likes": [len(posts) for posts in user_likes.values()],
                    }
                )
                st.dataframe(likes_df.sort_values(by="Likes", ascending=False))

            with col2:
                st.subheader("Comments by user:")
                comments_df = pd.DataFrame(
                    list(user_comments.items()), columns=["User", "Comments"]
                )
                st.dataframe(comments_df.sort_values(by="Comments", ascending=False))

            average_likes_per_user = total_likes / len(user_likes)
            st.subheader("Average Likes per User")
            st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

            st.subheader("Percentile:")
            percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            percentiles_values_likes = np.percentile(likes_df["Likes"], percentiles)
            percentiles_values_comments = np.percentile(
                comments_df["Comments"], percentiles
            )

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Likes Percentiles")
                for percentile, value in zip(percentiles, percentiles_values_likes):
                    st.write(f"{percentile}th percentile: {value}")

            with col2:
                st.subheader("Comments Percentiles")
                for percentile, value in zip(percentiles, percentiles_values_comments):
                    st.write(f"{percentile}th percentile: {value}")

            max_comments_resource_uuid = max(resource_comments, key=resource_comments.get)
            st.write(f"Resource UUID with the most comments: {max_comments_resource_uuid}")

            end_time = time.perf_counter()
            execution_time = end_time - start_time
            st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Please enter your access token")


if __name__ == "__main__":
    main()
