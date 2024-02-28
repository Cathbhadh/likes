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

            col3 = st.columns(1)[0]
            with col3:
                st.subheader("Comments by resource_uuid:")
                resource_comments_df = pd.DataFrame(
                    list(resource_comments.items()),
                    columns=["Resource UUID", "Comments"],
                )
                resource_comments_df = resource_comments_df.sort_values(
                    by="Comments", ascending=False
                )
                st.dataframe(resource_comments_df)

                most_commented_resource_uuid = resource_comments_df.iloc[0][
                    "Resource UUID"
                ]
                most_comments_count = resource_comments_df.iloc[0]["Comments"]
                st.subheader("Most Commented Post:")
                st.write(f"Post ID: {most_commented_resource_uuid}")
                st.write(f"Number of Comments: {most_comments_count}")

            col4 = st.columns(1)[0]
            with col4:
                st.subheader("Collected by resource_uuid:")
                resource_collected_df = pd.DataFrame(
                    list(resource_collected.items()),
                    columns=["Resource UUID", "Collected"],
                )
                resource_collected_df = resource_collected_df.sort_values(
                    by="Collected", ascending=False
                )
                st.dataframe(resource_collected_df)

                most_collected_resource_uuid = resource_collected_df.iloc[0][
                    "Resource UUID"
                ]
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
            st.subheader("% of Likes by Top Users")
            top_25_pct_users = likes_df.sort_values("Likes", ascending=False).head(int(0.25*len(likes_df)))
            pct_top_users = len(top_25_pct_users)/len(likes_df)*100
            pct_likes_top_users = top_25_pct_users['Likes'].sum()/total_likes*100
            st.write(f"{len(top_25_pct_users)} users ({pct_top_users:.1f}% of all users) contributed {pct_likes_top_users:.1f}% of total likes")
            top_10pct_users = likes_df.sort_values("Likes", ascending=False).head(int(0.1 * len(likes_df)))
            top_50pct_users = likes_df.sort_values("Likes", ascending=False).head(int(0.5 * len(likes_df)))
            bottom_25pct_users = likes_df.sort_values("Likes").head(int(0.25 * len(likes_df)))
            mid_users = likes_df.sort_values("Likes").iloc[int(0.5 * len(likes_df)):int(0.75 * len(likes_df))]
            
            # Displaying results
            pct_top_10_users = len(top_10pct_users) / len(likes_df) * 100
            pct_top_50_users = len(top_50pct_users) / len(likes_df) * 100
            pct_bottom_25_users = len(bottom_25pct_users) / len(likes_df) * 100
            pct_mid_users = len(mid_users) / len(likes_df) * 100
            
            st.write(f"{len(top_10pct_users)} users ({pct_top_10_users:.1f}% of all users) in the top 10%")
            st.write(f"{len(top_50pct_users)} users ({pct_top_50_users:.1f}% of all users) in the top 50%")
            st.write(f"{len(bottom_25pct_users)} users ({pct_bottom_25_users:.1f}% of all users) in the bottom 25%")
            st.write(f"{len(mid_users)} users ({pct_mid_users:.1f}% of all users) in the middle 25% (50% to 75%)")

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
            likes_df = pd.DataFrame({'User': ['A', 'B', 'C', 'D', 'E'], 
                         'Likes': [100, 60, 30, 15, 5]})

            total_likes = likes_df['Likes'].sum()


            end_time = time.perf_counter()
            execution_time = end_time - start_time
            st.write(f"Execution time: {execution_time} seconds")

    else:
        st.warning("Enter your access token:")


if __name__ == "__main__":
    main()
