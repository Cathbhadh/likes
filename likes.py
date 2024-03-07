from collections import defaultdict, Counter
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
    created_at = notification["created_at"]

    user_likes[name][(resource_uuid, created_at)] += 1

def process_commented_notification(notification, user_comments, resource_comments):
    name = notification["user_profile"]["name"]
    resource_uuid = notification["resource_uuid"]

    user_comments[name] += 1
    resource_comments[resource_uuid] += 1

def process_collected_notification(notification, resource_collected):
    resource_uuid = notification["resource_uuid"]
    resource_collected[resource_uuid] += 1

def generate_likes_dataframe(user_likes):
    liked_data = []

    for user, liked_posts in user_likes.items():
        for (resource_uuid, created_at), count in liked_posts.items():
            liked_data.extend(
                [
                    {
                        "actor_uuid": user,
                        "resource_uuid": resource_uuid,
                        "created_at": created_at,
                    }
                ]
                * count
            )

    likes_df = pd.DataFrame(liked_data)
    likes_df["created_at"] = pd.to_datetime(likes_df["created_at"])
    likes_df = likes_df.sort_values(by="created_at", ascending=False)

    return likes_df

def display_top_users_stats(df, percentile, total_count, label):
    top_users = df.head(int(percentile * len(df)))
    pct_top_users = len(top_users) / len(df) * 100
    pct_top_count = top_users[label].sum() / total_count * 100
    st.write(
        f"{len(top_users)} users ({pct_top_users:.1f}% of all users) contributed {pct_top_count:.1f}% of total {label.lower()}"
    )

def get_most_interacted_resource(resource_interaction, label):
    resource_interaction_df = pd.DataFrame.from_dict(resource_interaction, orient="index").reset_index()
    resource_interaction_df.columns = ["Resource UUID", label]
    resource_interaction_df = resource_interaction_df.sort_values(by=label, ascending=False)

    most_interacted_resource_uuid = resource_interaction_df.iloc[0]["Resource UUID"]
    most_interacted_count = resource_interaction_df.iloc[0][label]

    return most_interacted_resource_uuid, most_interacted_count

def print_stats(stats_dict, label):
    st.subheader(f"{label} by User:")
    stats_df = pd.DataFrame.from_dict(stats_dict, orient="index").reset_index()
    stats_df.columns = ["User", label]
    stats_df = stats_df.sort_values(by=label, ascending=False)
    st.dataframe(stats_df)

def load_data(session):
    offset = 0
    user_likes = defaultdict(Counter)
    user_comments = Counter()
    resource_comments = Counter()
    resource_collected = Counter()

    while True:
        resp = session.get(API_URL, params={"offset": offset, "limit": LIMIT})
        data = resp.json()

        for notification in data.get("notifications", []):
            if notification["action"] == "liked" and notification.get("resource_media"):
                process_liked_notification(notification, user_likes)

            if notification["action"] == "commented":
                process_commented_notification(
                    notification, user_comments, resource_comments
                )

            if notification["action"] == "collected":
                process_collected_notification(notification, resource_collected)

        if len(data.get("notifications", [])) < LIMIT:
            break

        offset += LIMIT

    return user_likes, user_comments, resource_comments, resource_collected

def main():
    access_token = st.text_input("Enter your access token")

    if access_token:
        session = authenticate_with_token(access_token)

        if st.button("Load Data"):
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

            col1, col2 = st.columns(2)

            with col1:
                likes_df = pd.DataFrame(
                    {
                        "User": list(user_likes.keys()),
                        "Likes": [sum(counter.values()) for counter in user_likes.values()],
                    }
                ).set_index("User")
                likes_df = likes_df.sort_values(by="Likes", ascending=False)
                st.dataframe(likes_df)

            with col2:
                print_stats(user_comments, "Comments")

            col3, col4 = st.columns(2)

            with col3:
                print_stats(resource_comments, "Comments")
                most_commented_resource_uuid, most_comments_count = get_most_interacted_resource(
                    resource_comments, "Comments"
                )

                st.subheader("Most Commented Post:")
                st.write(f"Post ID: {most_commented_resource_uuid}")
                st.write(f"Number of Comments: {most_comments_count}")

            with col4:
                print_stats(resource_collected, "Collected")
                most_collected_resource_uuid, most_collected_count = get_most_interacted_resource(
                    resource_collected, "Collected"
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
                pd.Series(user_comments.values()), percentiles
            )

            col5, col6 = st.columns(2)

            with col5:
                st.subheader("Likes Percentiles")
                for percentile, value in zip(percentiles, percentiles_values_likes):
                    rounded_value = round(value, 2)
                    st.write(f"{percentile}th percentile: {rounded_value}")

            with col6:
                st.subheader("Comments Percentiles")
                for percentile, value in zip(percentiles, percentiles_values_comments):
                    rounded_value = round(value, 2)
                    st.write(f"{percentile}th percentile: {rounded_value}")

            st.subheader("% of Likes by Top Users")
            display_top_users_stats(likes_df, 0.05, total_likes, "Likes")
            display_top_users_stats(likes_df, 0.10, total_likes, "Likes")
            display_top_users_stats(likes_df, 0.25, total_likes, "Likes")
            display_top_users_stats(likes_df, 0.50, total_likes, "Likes")

            likes_df = generate_likes_dataframe(user_likes)
            st.subheader("Likes by User:")
            st.dataframe(likes_df, hide_index=True)

            end_time = time.perf_counter()
            execution_time = end_time - start_time
            st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Enter your access token:")

if __name__ == "__main__":
    main()
    
