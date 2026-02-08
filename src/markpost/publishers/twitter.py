from __future__ import annotations

import tweepy

from markpost.config import TwitterConfig

TWITTER_CHAR_LIMIT = 280


def post_to_twitter(parts: list[str], config: TwitterConfig) -> list[str]:
    """Post a single tweet or a thread to Twitter/X.

    Returns a list of tweet IDs.
    """
    client = tweepy.Client(
        consumer_key=config.api_key,
        consumer_secret=config.api_secret,
        access_token=config.access_token,
        access_token_secret=config.access_token_secret,
    )

    tweet_ids: list[str] = []
    previous_id: str | None = None

    for part in parts:
        kwargs: dict = {"text": part}
        if previous_id is not None:
            kwargs["in_reply_to_tweet_id"] = previous_id

        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        tweet_ids.append(tweet_id)
        previous_id = tweet_id

    return tweet_ids
