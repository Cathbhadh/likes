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
    actor_uuid = notification["actor_uuid"]
    resource_uuid = notification["resource_uuid"]
    created_at = notification["created_at"]

    user_likes.append({
        "actor_uuid": actor_uuid,
        "resource_uuid": resource_uuid,
        "created_at": created_at
    })


def process_commented_notification(notification, user_comments, resource_comments):
    name = notification["user_profile"]["name"]
    resource_uuid = notification["resource_uuid"]

    user_comments[name] += 1
    resource_comments[resource_uuid] += 1

def process_collected_notification(notification, resource_collected):
    resource_uuid = notification["resource_uuid"]
    resource_collected[resource_uuid] += 1

def generate_likes_dataframe(user_likes):
    likes_df = pd.DataFrame(user_likes)
    likes_df["created_at"] = pd.to_datetime(likes_df["created_at"])
    likes_df = likes_df.sort_values(by="created_at", ascending=False)

    return likes_df

def get_followers(session, user_id, limit=100):
    followers_url = f"https://api.yodayo.com/v1/users/{user_id}/followers"
    params = {"offset": 0, "limit": limit, "width": 600, "include_nsfw": True}
    resp = session.get(followers_url, params=params)
    follower_data = resp.json()
    followers = [user["profile"]["name"] for user in follower_data["users"]]
    return followers

def analyze_likes(user_likes, followers):
    likes_df = generate_likes_dataframe(user_likes)
    
    # Users who didn't leave any likes
    no_likes_users = [user for user in user_likes.keys() if sum(user_likes[user].values()) == 0]
    st.write(f"Users who didn't leave any likes: {no_likes_users}")

    # Percentage of followers who left different numbers of likes
    follower_likes = likes_df[likes_df["actor_uuid"].isin(followers)]
    follower_like_counts = follower_likes.groupby("actor_uuid")["resource_uuid"].count()

    # Ensure follower_like_counts is a numeric series
    if follower_like_counts.dtypes != 'int64':
        st.warning("Error: Follower like counts are not numeric. Skipping percentile analysis.")
    elif len(follower_like_counts) == 0:
        st.warning("No followers have left any likes. Skipping percentile analysis.")
    else:
        like_count_percentiles = [0, 1, 5, 10, 25, 50, 75, 90, 95, 100]
        for pct in like_count_percentiles:
            try:
                count = follower_like_counts.quantile(pct/100)
                pct_users = len(follower_like_counts[follower_like_counts <= count]) / len(follower_like_counts) * 100
                st.write(f"{pct}% of followers left <= {count} likes")
            except Exception as e:
                st.warning(f"Error occurred while calculating {pct}th percentile: {e}")

    # Proportion of likes from followers vs non-followers
    if len(follower_likes) == 0:
        follower_likes_count = 0
        follower_like_proportion = 0
    else:
        follower_likes_count = len(follower_likes)
        total_likes_count = len(likes_df)
        follower_like_proportion = follower_likes_count / total_likes_count * 100

    total_likes_count = len(likes_df)
    follower_like_proportion = follower_likes_count / total_likes_count * 100 if total_likes_count > 0 else 0
    non_follower_like_proportion = 100 - follower_like_proportion
    st.write(f"{follower_like_proportion:.2f}% of likes came from followers")
    st.write(f"{non_follower_like_proportion:.2f}% of likes came from non-followers")



def load_data(session):
    offset = 0
    user_likes = []  # Use a regular list instead of defaultdict
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
    user_id = st.text_input("Enter user ID")

    if access_token and user_id:
        session = authenticate_with_token(access_token)

        start_time = time.perf_counter()
        (
            user_likes,
            user_comments,
            resource_comments,
            resource_collected,
        ) = load_data(session)

        total_likes = sum(1 for user_like in user_likes for _ in [None])
        total_comments = sum(user_comments.values())

        st.subheader("Total Likes and Comments")
        st.write(f"Total Likes: {total_likes}")
        st.write(f"Total Comments: {total_comments}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Likes by user:")
            likes_by_user = {}
            for user_like in user_likes:
                actor_uuid = user_like["actor_uuid"]
                likes_by_user[actor_uuid] = likes_by_user.get(actor_uuid, 0) + 1

            likes_df = pd.DataFrame(
                {
                    "User": list(likes_by_user.keys()),
                    "Likes": list(likes_by_user.values()),
                }
            )
            likes_df = likes_df.sort_values(by="Likes", ascending=False)
            st.dataframe(likes_df, hide_index=True)

        with col2:
            st.subheader("Comments by user:")
            comments_df = pd.DataFrame.from_dict(user_comments, orient="index", columns=["Comments"]).reset_index()
            comments_df = comments_df.rename(columns={'index': 'User'})
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
            st.dataframe(resource_comments_df, hide_index=True)

            most_commented_resource_uuid = resource_comments_df.iloc[0]["Resource UUID"]
            most_comments_count = resource_comments_df.iloc[0]["Comments"]

            st.subheader("Most Commented Post:")
            st.write(f"Post ID: {most_commented_resource_uuid}")
            st.write(f"Number of Comments: {most_comments_count}")

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
            st.dataframe(resource_collected_df, hide_index=True)

            most_collected_resource_uuid = resource_collected_df.iloc[0]["Resource UUID"]
            most_collected_count = resource_collected_df.iloc[0]["Collected"]

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
                rounded_value = round(value, 2)
                st.write(f"{percentile}th percentile: {rounded_value}")

        with col6:
            st.subheader("Comments Percentiles")
            for percentile, value in zip(percentiles, percentiles_values_comments):
                rounded_value = round(value, 2)
                st.write(f"{percentile}th percentile: {rounded_value}")

        likes_df = generate_likes_dataframe(user_likes)
        st.subheader("Likes by User:")
        st.dataframe(likes_df, hide_index=True)

        followers = get_followers(session, user_id)
        analyze_likes(user_likes, followers)

        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Enter your access token and user ID:")

if __name__ == "__main__":
    main()
