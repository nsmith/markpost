# tests/test_twitter.py
from unittest.mock import MagicMock, patch, call


def test_post_single_tweet():
    from markpost.config import TwitterConfig
    from markpost.publishers.twitter import post_to_twitter

    mock_response = MagicMock()
    mock_response.data = {"id": "111"}

    with patch("markpost.publishers.twitter.tweepy.Client") as MockClient:
        client = MockClient.return_value
        client.create_tweet.return_value = mock_response

        config = TwitterConfig(
            api_key="k", api_secret="s",
            access_token="a", access_token_secret="as",
        )
        result = post_to_twitter(["Hello world"], config)

    client.create_tweet.assert_called_once_with(text="Hello world")
    assert result == ["111"]


def test_post_thread():
    from markpost.config import TwitterConfig
    from markpost.publishers.twitter import post_to_twitter

    responses = []
    for tweet_id in ["111", "222", "333"]:
        r = MagicMock()
        r.data = {"id": tweet_id}
        responses.append(r)

    with patch("markpost.publishers.twitter.tweepy.Client") as MockClient:
        client = MockClient.return_value
        client.create_tweet.side_effect = responses

        config = TwitterConfig(
            api_key="k", api_secret="s",
            access_token="a", access_token_secret="as",
        )
        result = post_to_twitter(["Part 1", "Part 2", "Part 3"], config)

    assert client.create_tweet.call_count == 3
    # First tweet has no reply
    client.create_tweet.assert_any_call(text="Part 1")
    # Subsequent tweets reply to the previous
    client.create_tweet.assert_any_call(text="Part 2", in_reply_to_tweet_id="111")
    client.create_tweet.assert_any_call(text="Part 3", in_reply_to_tweet_id="222")
    assert result == ["111", "222", "333"]
