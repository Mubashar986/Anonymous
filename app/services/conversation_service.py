"""
Service Layer for Conversation and Message business logic and authorization.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import WS_MAX_TEXT_LEN
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User, UserRole
from app.repositories.conversation_repository import conversation_repository
from app.repositories.message_repository import message_repository
from app.services.follow_service import follow_service
from app.repositories.user_repository import user_repository
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Domain authorization service for 1-to-1 direct messaging conversations.
    """

    async def start_conversation(
        self, db: AsyncSession, current_user: User, target_user_id: uuid.UUID
    ) -> Conversation:
        """
        Initiate or retrieve a 1-to-1 conversation with target_user_id.
        Enforces FollowService.can_send_dm authorization policy.
        """
        if current_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start a conversation with yourself",
            )

        if current_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrators cannot participate in direct conversations",
            )

        target_user = await user_repository.get_by_id(db, target_user_id)
        if not target_user or not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found or inactive",
            )

        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot start conversation with an administrator",
            )

        can_dm = await follow_service.can_send_dm(db, current_user.id, target_user_id)
        if not can_dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="An active follow relationship is required to start a conversation",
            )

        return await conversation_repository.get_or_create_for_pair(
            db, current_user.id, target_user_id
        )

    async def send_message(
        self,
        db: AsyncSession,
        current_user: User,
        conversation_id: uuid.UUID,
        client_msg_id: uuid.UUID,
        text: str,
    ) -> Message:
        """
        Send and store a direct message within conversation_id.
        Validates membership, follow authorization, and text payload bounds.
        """
        if current_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrators cannot send direct messages",
            )

        conv = await conversation_repository.get_by_id(db, conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        is_part = await conversation_repository.is_participant(
            db, conversation_id, current_user.id
        )
        if not is_part:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )

        # Identify recipient
        other_participants = [
            p for p in conv.participants if p.user_id != current_user.id
        ]
        if not other_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation participant structure",
            )
        recipient_id = other_participants[0].user_id

        can_dm = await follow_service.can_send_dm(db, current_user.id, recipient_id)
        if not can_dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot send message. Active follow relationship has been removed.",
            )

        clean_text = text.strip() if text else ""
        if not clean_text or len(clean_text) > WS_MAX_TEXT_LEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message text must be between 1 and {WS_MAX_TEXT_LEN} characters",
            )

        msg = await message_repository.create(
            db,
            conversation_id=conversation_id,
            sender_id=current_user.id,
            client_msg_id=client_msg_id,
            text=clean_text,
        )

        # Emit notification to recipient
        await notification_service.create_notification_event(
            db=db,
            recipient_id=recipient_id,
            actor_id=current_user.id,
            actor_username=current_user.username,
            event_type=NotificationTypeEnum.NEW_DIRECT_MESSAGE,
            target_type="message",
            target_id=msg.id,
            title="New Direct Message",
            summary_text=f"@{current_user.username} sent you a direct message.",
            navigation_target=NavigationTargetEnum.DM_CONVERSATION,
            navigation_params={"conversation_id": str(conversation_id)},
        )

        return msg

    async def get_conversation_history(
        self,
        db: AsyncSession,
        current_user: User,
        conversation_id: uuid.UUID,
        before_timestamp: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Message]:
        """
        Retrieve paginated chat history for a conversation participant.
        """
        is_part = await conversation_repository.is_participant(
            db, conversation_id, current_user.id
        )
        if not is_part:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation history",
            )

        return await message_repository.get_history(
            db, conversation_id, before_timestamp, limit
        )

    async def list_user_conversations(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 20
    ) -> List[Conversation]:
        """
        List all active conversations for the authenticated user.
        """
        return await conversation_repository.get_user_conversations(
            db, current_user.id, skip, limit
        )


conversation_service = ConversationService()
