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


def process_notification(
    notification, user_likes, user_comments, resource_comments, resource_collected
):
    action = notification["action"]
    user_profile = notification["user_profile"]
    resource_uuid = notification["resource_uuid"]

    if action == "liked" and notification.get("resource_media"):
        user_likes.setdefault(user_profile["name"], set()).add(resource_uuid)

    if action == "commented":
        user_comments[user_profile["name"]] = (
            user_comments.get(user_profile["name"], 0) + 1
        )
        resource_comments[resource_uuid] = resource_comments.get(resource_uuid, 0) + 1

    if action == "collected":
        resource_collected[resource_uuid] = resource_collected.get(resource_uuid, 0) + 1


def display_top_users_stats(df, percentile, total_likes):
    top_users = df.sort_values("Likes", ascending=False).head(int(percentile * len(df)))
    pct_top_users = len(top_users) / len(df) * 100
    pct_likes_top_users = top_users["Likes"].sum() / total_likes * 100
    st.write(
        f"{len(top_users)} users ({pct_top_users:.1f}% of all users) contributed {pct_likes_top_users:.1f}% of total likes"
    )


def load_data(session):
    offset, user_likes, user_comments, resource_comments, resource_collected = (
        0,
        {},
        {},
        {},
        {},
    )

    while True:
        resp = session.get(API_URL, params={"offset": offset, "limit": LIMIT})
        data = resp.json()

        for notification in data.get("notifications", []):
            process_notification(
                notification,
                user_likes,
                user_comments,
                resource_comments,
                resource_collected,
            )

        if len(data.get("notifications", [])) < LIMIT:
            break

        offset += LIMIT

    return user_likes, user_comments, resource_comments, resource_collected


def main():
    access_token = st.text_input("Enter your access token")

    if access_token and st.button("Load Data"):
        session = authenticate_with_token(access_token)
        start_time = time.perf_counter()

        (
            user_likes,
            user_comments,
            resource_comments,
            resource_collected,
        ) = load_data(session)

        total_likes = sum(len(posts) for posts in user_likes.values())
        total_comments = sum(user_comments.values())

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        col1, col2, col3, col4 = st.columns(4)

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

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Comments by resource_uuid:")
            resource_comments_df = pd.DataFrame(
                list(resource_comments.items()), columns=["Resource UUID", "Comments"]
            ).sort_values(by="Comments", ascending=False)
            st.dataframe(resource_comments_df)
            most_commented_resource_uuid, most_comments_count = (
                resource_comments_df.iloc[0]["Resource UUID"],
                resource_comments_df.iloc[0]["Comments"],
            )
            st.subheader("Most Commented Post:")
            st.write(f"Post ID: {most_commented_resource_uuid}")
            st.write(f"Number of Comments: {most_comments_count}")

        with col4:
            st.subheader("Collected by resource_uuid:")
            resource_collected_df = pd.DataFrame(
                list(resource_collected.items()), columns=["Resource UUID", "Collected"]
            ).sort_values(by="Collected", ascending=False)
            st.dataframe(resource_collected_df)
            most_collected_resource_uuid, most_collected_count = (
                resource_collected_df.iloc[0]["Resource UUID"],
                resource_collected_df.iloc[0]["Collected"],
            )
            st.subheader("Most Collected Post:")
            st.write(f"Post ID: {most_collected_resource_uuid}")
            st.write(f"Number of Collections: {most_collected_count}")

        st.subheader("User Interaction Statistics:")
        st.write(f"Number of Users who Liked: {len(user_likes)}")
        st.write(f"Number of Users who Commented: {len(user_comments)}")
        st.write(f"Number of Users who Collected: {len(resource_collected)}")

        average_likes_per_user = total_likes / len(user_likes)
        st.subheader("Average Likes per User")
        st.write(f"Average Likes per User: {average_likes_per_user:.2f}")

        st.subheader("Percentile:")
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentiles_values_likes = np.percentile(likes_df["Likes"], percentiles)
        percentiles_values_comments = np.percentile(
            comments_df["Comments"], percentiles
        )

        col5, col6 = st.columns(2)

        with col5:
            st.subheader("Likes Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_likes):
                st.write(f"{percentile}th percentile: {round(value, 2)}")

        with col6:
            st.subheader("Comments Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_comments):
                st.write(f"{percentile}th percentile: {round(value, 2)}")

        st.subheader("% of Likes by Top Users")
        display_top_users_stats(likes_df, 0.10, total_likes)
        display_top_users_stats(likes_df, 0.25, total_likes)
        display_top_users_stats(likes_df, 0.50, total_likes)

        end_time = time.perf_counter()
        st.write(f"Execution time: {end_time - start_time} seconds")

    else:
        st.warning("Enter your access token:")


if __name__ == "__main__":
    main()
