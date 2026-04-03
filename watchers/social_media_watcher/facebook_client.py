"""
Facebook Client

Handles posting and engagement retrieval for Facebook using facebook-sdk.
"""

import facebook
from typing import Dict, Any, List, Optional
import logging

from watchers.shared.env_loader import get_loader

logger = logging.getLogger(__name__)

class FacebookClient:
    def __init__(self):
        self.graph: Optional[facebook.GraphAPI] = None
        self.connected = False
        self.page_id: Optional[str] = None

    def connect(self) -> bool:
        try:
            loader = get_loader()
            credentials = loader.get_facebook_credentials()
            access_token = credentials["access_token"]
            self.page_id = credentials["page_id"]

            if not access_token:
                logger.error("Missing Facebook access token")
                return False

            if not self.page_id:
                logger.error("Missing Facebook page ID")
                return False

            self.graph = facebook.GraphAPI(access_token=access_token, version="3.1")
            self.connected = True
            logger.info(f"Connected to Facebook page: {self.page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Facebook: {e}")
            self.connected = False
            return False

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Facebook")
        if not self.page_id:
            raise ConnectionError("Page ID not configured")
        try:
            if media_urls:
                result = self.graph.put_photo(
                    image=open(media_urls[0], 'rb'),
                    album_path=f"{self.page_id}/photos",
                    message=content
                )
            else:
                result = self.graph.put_object(
                    parent_object=self.page_id,
                    connection_name="feed",
                    message=content
                )
            post_id = result.get("id", result.get("post_id"))
            logger.info(f"Posted to Facebook page {self.page_id}: {post_id}")
            return {"success": True, "post_id": post_id}
        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            return {"success": False, "error": str(e)}

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Facebook")
        try:
            post = self.graph.get_object(id=post_id, fields="likes.summary(true),comments.summary(true),shares")
            likes = post.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
            shares = post.get("shares", {}).get("count", 0)
            return {"likes": likes, "comments": comments, "shares": shares, "reach": 0}
        except Exception as e:
            logger.error(f"Failed to get Facebook engagement: {e}")
            return {"likes": 0, "comments": 0, "shares": 0, "reach": 0}

    def delete_post(self, post_id: str) -> bool:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Facebook")
        try:
            self.graph.delete_object(id=post_id)
            logger.info(f"Deleted Facebook post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Facebook post: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            return {"connected": False, "error": "Not connected"}
        try:
            me = self.graph.get_object(id="me", fields="name,id")
            return {"connected": True, "user": me}
        except Exception as e:
            return {"connected": False, "error": str(e)}
