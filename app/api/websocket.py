"""WebSocket API endpoint."""
from fastapi import APIRouter, WebSocket, Query
import uuid
import json
import logging
from app.database import AsyncSessionLocal
from app.core import ConnectionManager, decode_token
from app.services import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

manager = ConnectionManager()


@router.websocket("/api/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time task updates and chat."""
    # Verify token
    token_data = decode_token(token)
    if not token_data:
        logger.warning("WebSocket connection rejected: Invalid token")
        await websocket.close(code=4001, reason="Invalid token")
        return

    # token_data["user_id"] is already a UUID object
    user_id = token_data.get("user_id")
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    logger.info(f"WebSocket connection established for user {user_id}")

    await manager.connect(user_id, websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            logger.info(f"Received WebSocket message: {message_data}")

            # Handle ping/pong for bidirectional testing
            if message_data.get("type") == "ping":
                logger.info("Received ping, sending pong")
                await manager.send_personal_message(user_id, {
                    "type": "pong",
                    "data": {"timestamp": message_data.get("timestamp")}
                })
                continue

            # Create database session for this message
            async with AsyncSessionLocal() as db:
                chat_service = ChatService(db)

                # Parse session_id properly
                session_id = message_data.get("session_id")
                if session_id and isinstance(session_id, str):
                    try:
                        session_id = uuid.UUID(session_id)
                    except ValueError:
                        logger.warning(f"Invalid session_id format: {session_id}")
                        session_id = None

                # Process chat message through orchestrator
                result = await chat_service.process_message(
                    user_id=user_id,
                    message=message_data.get("message", ""),
                    session_id=session_id,
                )

                logger.info(f"Chat service result: {result}")

                # Send response with correct structure
                response = {
                    "type": "chat_response",
                    "data": {
                        "response": result.get("message", ""),
                        "message": result.get("message", ""),
                        "intent": result.get("intent"),
                        "success": result.get("success", True),
                        "data": result.get("data"),
                    },
                }

                await manager.send_personal_message(user_id, response)
                logger.info(f"Sent WebSocket response to user {user_id}")

    except json.JSONDecodeError as e:
        logger.error(f"WebSocket JSON decode error: {e}")
        error_response = {
            "type": "error",
            "data": {"error": "Invalid message format"}
        }
        await manager.send_personal_message(user_id, error_response)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        error_response = {
            "type": "error",
            "data": {"error": str(e)}
        }
        try:
            await manager.send_personal_message(user_id, error_response)
        except:
            pass
    finally:
        logger.info(f"WebSocket connection closed for user {user_id}")
        await manager.disconnect(user_id)
