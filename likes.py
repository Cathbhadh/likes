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

    user_comments[name] = user_comments.get(name, 0) + 1

    resource_uuid = notification["resource_uuid"]
    resource_comments[resource_uuid] = resource_comments.get(resource_uuid, 0) + 1


def process_collected_notification(notification, resource_collected):
    resource_uuid = notification["resource_uuid"]
    resource_collected[resource_uuid] = resource_collected.get(resource_uuid, 0) + 1


def display_top_users_stats(likes_df, percentile, total_likes):
    top_users = likes_df.sort_values("Likes", ascending=False).head(
        int(percentile * len(likes_df))
    )
    pct_top_users = len(top_users) / len(likes_df) * 100
    pct_likes_top_users = top_users["Likes"].sum() / total_likes * 100
    st.write(
        f"{len(top_users)} users ({pct_top_users:.1f}% of all users) contributed {pct_likes_top_users:.1f}% of total likes"
    )

def display_dataframe_info(title, df, sort_column, additional_info=None):
    st.subheader(title)
    st.dataframe(df.sort_values(by=sort_column, ascending=False))

    if additional_info:
        st.subheader(additional_info['title'])
        st.write(f"{additional_info['id_label']}: {additional_info['id_value']}")
        st.write(f"{additional_info['count_label']}: {additional_info['count_value']}")


def load_data(session):
    offset = 0
    user_likes = {}
    user_comments = {}
    resource_comments = {}
    resource_collected = {}

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
            likes_df = pd.DataFrame(
                    {
                        "User": list(user_likes.keys()),
                        "Likes": [len(posts) for posts in user_likes.values()],
                    }
                )
            comments_df = pd.DataFrame(
                    list(user_comments.items()), columns=["User", "Comments"]
                )

            st.subheader("Total Likes and Comments")
            st.write(f"Total Likes: {total_likes}")
            st.write(f"Total Comments: {total_comments}")

            col1, col2, col3, col4 = st.columns(4)

            display_dataframe_info("Likes by user:", likes_df, "Likes", additional_info=None)
            display_dataframe_info("Comments by user:", comments_df, "Comments", additional_info=None)

            most_commented_info = {
                'title': 'Most Commented Post:',
                'id_label': 'Post ID',
                'id_value': most_commented_resource_uuid,
                'count_label': 'Number of Comments',
                'count_value': most_comments_count
            }
            display_dataframe_info("Comments by resource_uuid:", resource_comments_df, "Comments", most_commented_info)

            most_collected_info = {
                'title': 'Most Collected Post:',
                'id_label': 'Post ID',
                'id_value': most_collected_resource_uuid,
                'count_label': 'Number of Collections',
                'count_value': most_collected_count
            }
            display_dataframe_info("Collected by resource_uuid:", resource_collected_df, "Collected", most_collected_info)

            user_interaction_info = {
                'title': 'User Interaction Statistics:',
                'id_label': 'User Type',
                'id_value': None,
                'count_label': 'Number of Users',
                'count_value': None
            }
            st.subheader(user_interaction_info['title'])
            st.write(f"{user_interaction_info['count_label']} who Liked: {len(user_likes)}")
            st.write(f"{user_interaction_info['count_label']} who Commented: {len(user_comments)}")
            st.write(f"{user_interaction_info['count_label']} who Collected: {len(resource_collected)}")


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

            st.subheader("% of Likes by Top Users")
            display_top_users_stats(likes_df, 0.10, total_likes)
            display_top_users_stats(likes_df, 0.25, total_likes)
            display_top_users_stats(likes_df, 0.50, total_likes)

            end_time = time.perf_counter()
            execution_time = end_time - start_time
            st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Enter your access token:")


if __name__ == "__main__":
    main()
