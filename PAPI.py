import requests
import pandas as pd
import json
import re
import time


def get_steam_reviews(appid, n=100):
    url = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"

    headers = {
        "User-Agent": "student-project/1.0",
        "Accept": "application/json"
    }

    reviews = []
    seen_ids = set()
    seen_cursors = set()
    cursor = "*"

    while len(reviews) < n:
        params = {
            "input_json": json.dumps({
                "appid": appid,
                "num_per_page": min(100, n - len(reviews)),
                "cursor": cursor,
                "filter": "recent"
            })
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()

        data = response.json().get("response", {})
        batch = data.get("reviews", [])

        if not batch:
            break

        for item in batch:
            review_id = item.get("recommendationid")

            if review_id is not None:
                unique_id = str(review_id)
            else:
                unique_id = (
                    str(appid),
                    item.get("language", ""),
                    item.get("review", "").strip()
                )

            if unique_id in seen_ids:
                continue

            seen_ids.add(unique_id)

            review_text = re.sub(
                r"\s+",
                " ",
                item.get("review", "")
            ).strip()

            reviews.append({
                "appid": appid,
                "review": review_text,
                "language": item.get("language", ""),
                "voted_up": item.get("voted_up")
            })

            if len(reviews) >= n:
                break

        next_cursor = data.get("cursor")

        if not next_cursor or next_cursor == cursor:
            break

        if next_cursor in seen_cursors:
            break

        seen_cursors.add(next_cursor)
        cursor = next_cursor

        time.sleep(0.2)

    return pd.DataFrame(
        reviews,
        columns=["appid", "review", "language", "voted_up"]
    )


appids = [1809700, 1113000, 2161700, 1687950]

all_reviews = []

for appid in appids:
    df = get_steam_reviews(appid, n=100)
    all_reviews.append(df)

reviews_df = pd.concat(all_reviews, ignore_index=True)

reviews_df = reviews_df.drop_duplicates(
    subset=["appid", "review", "language"]
).reset_index(drop=True)

reviews_df.to_csv(
    "steam_reviews_persona.csv",
    index=False,
    encoding="utf-8-sig"
)

print(reviews_df.shape)
print(reviews_df["voted_up"].value_counts())