import asyncio
import aiohttp
from collections import defaultdict, Counter
import streamlit as st
import pandas as pd
import numpy as np
import time

API_URL = "https://api.yodayo.com/v1/notifications"
LIMIT = 500

def authenticate_with_token(access_token):
    session = aiohttp.ClientSession()
    jar = aiohttp.CookieJar()
    jar.update_cookies({"access_token": access_token})
    session.cookie_jar = jar
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

@st.cache_data(ttl=7200)
def generate_likes_dataframe(user_likes):
    # ... (existing code) ...

@st.cache_data(ttl=7200)
def generate_comments_dataframe(user_comments, user_is_follower, notifications):
    # ... (existing code) ...

@st.cache_data(ttl=7200)
def get_followers(_session, user_id):
    # ... (existing code) ...

@st.cache_data(ttl=7200)
def analyze_likes(user_likes, followers, follower_like_counts):
    # ... (existing code) ...

async def fetch_notifications(session, offset, limit):
    params = {"offset": offset, "limit": limit}
    async with session.get(API_URL, params=params) as response:
        data = await response.json()
        return data.get("notifications", [])

async def process_notifications(session, notifications, user_likes, user_comments, resource_comments, resource_collected, follower_like_counts, user_is_follower):
    liked_notifications = [
        n
        for n in notifications
        if n["action"] == "liked" and n.get("resource_media")
    ]
    commented_notifications = [
        n for n in notifications if n["action"] == "commented"
    ]
    collected_notifications = [
        n for n in notifications if n["action"] == "collected"
    ]

    for notification in liked_notifications:
        process_liked_notification(notification, user_likes)
        name = notification["user_profile"]["name"]
        follower_like_counts[name] += 1

    for notification in commented_notifications:
        process_commented_notification(
            notification, user_comments, resource_comments
        )

    for notification in collected_notifications:
        process_collected_notification(notification, resource_collected)

async def main():
    access_token = st.text_input("Enter your access token")
    user_id = st.text_input("Enter user ID")

    if access_token and user_id:
        session = authenticate_with_token(access_token)
        followers = get_followers(session, user_id)
        start_time = time.perf_counter()

        user_likes = defaultdict(Counter)
        user_comments = Counter()
        resource_comments = Counter()
        resource_collected = Counter()
        follower_like_counts = Counter()
        user_is_follower = defaultdict(bool)

        for follower in followers:
            user_is_follower[follower] = True

        async with session as session:
            offset = 0
            while True:
                notifications = await fetch_notifications(session, offset, LIMIT)
                if not notifications:
                    break

                await process_notifications(session, notifications, user_likes, user_comments, resource_comments, resource_collected, follower_like_counts, user_is_follower)

                offset += LIMIT

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
                    "Likes": [sum(counter.values()) for counter in user_likes.values()],
                    "is_follower": [
                        user_is_follower[user] for user in user_likes.keys()
                    ],
                }
            )
            likes_df = likes_df.sort_values(by="Likes", ascending=False)
            st.dataframe(likes_df, hide_index=True)

        with col2:
            st.subheader("Comments by user:")
            comments_df = pd.DataFrame(
                {
                    "User": list(user_comments.keys()),
                    "Comments": list(user_comments.values()),
                    "is_follower": [
                        user_is_follower[user] for user in user_comments.keys()
                    ],
                }
            )
            comments_df = comments_df.sort_values(by="Comments", ascending=False)
            st.dataframe(comments_df, hide_index=True)

        col3 = st.columns(1)[0]
        with col3:
            st.subheader("Comments by resource_uuid:")
            resource_comments_df = pd.DataFrame.from_dict(
                resource_comments, orient="index"
            ).reset_index()
            resource_comments_df.columns = ["Resource UUID", "Comments"]
            resource_comments_df = resource_comments_df.sort_values(
                by="Comments", ascending=False
            )
            resource_comments_df["Resource UUID"] = (
                "https://yodayo.com/posts/" + resource_comments_df["Resource UUID"]
            )
            column_config = {
                "Resource UUID": st.column_config.LinkColumn(
                    "Link",
                    display_text="https://yodayo\.com/posts/(.*?)/",
                )
            }
            st.dataframe(
                resource_comments_df, hide_index=True, column_config=column_config
            )

        col4 = st.columns(1)[0]
        with col4:
            st.subheader("Collected by resource_uuid:")
            resource_collected_df = pd.DataFrame.from_dict(
                resource_collected, orient="index"
            ).reset_index()
            resource_collected_df.columns = ["Resource UUID", "Collected"]
            resource_collected_df = resource_collected_df.sort_values(
                by="Collected", ascending=False
            )
            resource_collected_df["Resource UUID"] = (
                "https://yodayo.com/posts/" + resource_collected_df["Resource UUID"]
            )

            column_config = {
                "Resource UUID": st.column_config.LinkColumn(
                    "Link", display_text="https://yodayo\.com/posts/(.*?)/"
                )
            }
            st.dataframe(
                resource_collected_df, hide_index=True, column_config=column_config
            )
            most_collected_resource_uuid = resource_collected_df.iloc[0][
                "Resource UUID"
            ]
            most_collected_count = resource_collected_df.iloc[0]["Collected"]

            st.subheader("Most Collected Post:")
            st.write(f"Post ID: {most_collected_resource_uuid}")
            st.write(f"№ of Collections: {most_collected_count}")
            st.subheader("User Interaction Statistics:")
            st.write(f"№ of Unique Users who Liked: {len(user_likes)}")
            st.write(f"№ of Unique Users who Commented: {len(user_comments)}")
            st.write(f"№ of Users who Collected: {len(resource_collected)}")

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
                rounded_value = round(value, 2)
                st.write(f"{percentile}th percentile: {rounded_value}")

        with col6:
            st.subheader("Comments Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_comments):
                rounded_value = round(value, 2)
                st.write(f"{percentile}th percentile: {rounded_value}")

        likes_df = generate_likes_dataframe(user_likes)
        comments_df = generate_comments_dataframe(
            user_comments, user_is_follower, notifications
        )
        column_config = {
            "actor_uuid": st.column_config.TextColumn(
                "Name",
            ),
            "resource_uuid": st.column_config.LinkColumn(
                "Link", display_text="https://yodayo\.com/posts/(.*?)/"
            ),
        }
        st.subheader("Likes by User:", help="Shows all notifications in order")
        st.dataframe(likes_df, hide_index=True, column_config=column_config)
        st.subheader("Comments by User:")
        query = st.text_input("Search comments by user")
        if query:
            mask = comments_df.applymap(lambda x: query.lower() in str(x).lower()).any(
                axis=1
            )
            filtered_comments_df = comments_df[mask]
        else:
            filtered_comments_df = comments_df
        column_config = {
            "actor_uuid": st.column_config.TextColumn(
                "Name",
            ),
            "resource_uuid": st.column_config.LinkColumn(
                "Link", display_text="https://yodayo\.com/posts/(.*?)/"
            ),
        }
        st.dataframe(filtered_comments_df, hide_index=True, column_config=column_config)
        analyze_likes(user_likes, followers, follower_like_counts)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Enter your access token and user ID:")

if __name__ == "__main__":
    asyncio.run(main())
