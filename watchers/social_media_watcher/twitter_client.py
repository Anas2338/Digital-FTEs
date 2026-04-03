"""
Twitter Client

Handles posting and engagement retrieval for Twitter using tweepy.
"""

import tweepy
from typing import Dict, Any, List, Optional
import logging

from watchers.shared.env_loader import get_loader

logger = logging.getLogger(__name__)

class TwitterClient:
    def __init__(self):
        self.api: Optional[tweepy.API] = None
        self.client: Optional[tweepy.Client] = None
        self.connected = False

    def connect(self) -> bool:
        try:
            loader = get_loader()
            credentials = loader.get_twitter_credentials()

            api_key = credentials["consumer_key"]
            api_secret = credentials["consumer_secret"]
            access_token = credentials["access_token"]
            access_secret = credentials["access_token_secret"]

            if not all([api_key, api_secret, access_token, access_secret]):
                logger.error("Missing Twitter credentials")
                return False

            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
            self.api = tweepy.API(auth)
            self.client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_secret)
            self.connected = True
            logger.info("Connected to Twitter")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Twitter: {e}")
            self.connected = False
            return False

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Twitter")
        try:
            response = self.client.create_tweet(text=content)
            tweet_id = response.data["id"]
            logger.info(f"Posted to Twitter: {tweet_id}")
            return {"success": True, "post_id": str(tweet_id)}
        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            return {"success": False, "error": str(e)}

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Twitter")
        try:
            tweet = self.client.get_tweet(id=post_id, tweet_fields=["public_metrics"])
            metrics = tweet.data.public_metrics
            return {
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "impressions": metrics.get("impression_count", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Twitter engagement: {e}")
            return {"likes": 0, "retweets": 0, "replies": 0, "impressions": 0}

    def delete_post(self, post_id: str) -> bool:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to Twitter")
        try:
            self.client.delete_tweet(id=post_id)
            logger.info(f"Deleted Twitter post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Twitter post: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        if not self.connected or not self.client:
            return {"connected": False, "error": "Not connected"}
        try:
            me = self.client.get_me()
            return {"connected": True, "user": {"username": me.data.username, "id": me.data.id}}
        except Exception as e:
            return {"connected": False, "error": str(e)}
