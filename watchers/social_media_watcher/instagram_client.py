"""
Instagram Client

Handles posting and engagement retrieval for Instagram using Instagram Graph API via facebook-sdk.
"""

import facebook
from typing import Dict, Any, List, Optional
import logging

from watchers.shared.env_loader import get_loader

logger = logging.getLogger(__name__)

class InstagramClient:
    def __init__(self):
        self.graph: Optional[facebook.GraphAPI] = None
        self.instagram_account_id: Optional[str] = None
        self.connected = False

    def connect(self) -> bool:
        try:
            loader = get_loader()
            credentials = loader.get_instagram_credentials()

            access_token = credentials["access_token"]
            instagram_account_id = credentials["account_id"]

            if not access_token or not instagram_account_id:
                logger.error("Missing Instagram credentials")
                return False

            self.graph = facebook.GraphAPI(access_token=access_token, version="3.1")
            self.instagram_account_id = instagram_account_id
            self.connected = True
            logger.info("Connected to Instagram")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Instagram: {e}")
            self.connected = False
            return False

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Instagram")
        try:
            if not media_urls:
                return {"success": False, "error": "Instagram requires media"}
            
            container = self.graph.put_object(parent_object=self.instagram_account_id, connection_name="media", image_url=media_urls[0], caption=content)
            container_id = container.get("id")
            
            result = self.graph.put_object(parent_object=self.instagram_account_id, connection_name="media_publish", creation_id=container_id)
            post_id = result.get("id")
            
            logger.info(f"Posted to Instagram: {post_id}")
            return {"success": True, "post_id": post_id}
        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}")
            return {"success": False, "error": str(e)}

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Instagram")
        try:
            media = self.graph.get_object(id=post_id, fields="like_count,comments_count")
            likes = media.get("like_count", 0)
            comments = media.get("comments_count", 0)
            engagement_rate = 0.0
            return {"likes": likes, "comments": comments, "engagement_rate": engagement_rate}
        except Exception as e:
            logger.error(f"Failed to get Instagram engagement: {e}")
            return {"likes": 0, "comments": 0, "engagement_rate": 0.0}

    def delete_post(self, post_id: str) -> bool:
        if not self.connected or not self.graph:
            raise ConnectionError("Not connected to Instagram")
        try:
            self.graph.delete_object(id=post_id)
            logger.info(f"Deleted Instagram post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Instagram post: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        if not self.connected or not self.graph:
            return {"connected": False, "error": "Not connected"}
        try:
            account = self.graph.get_object(id=self.instagram_account_id, fields="username,id")
            return {"connected": True, "account": account}
        except Exception as e:
            return {"connected": False, "error": str(e)}
