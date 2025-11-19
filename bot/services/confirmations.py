import time
import uuid

class ConfirmationManager:
    def __init__(self):
        self.pending_actions = {}

    def create(self, user_id: int, action_type: str, data: dict = None, timeout: int = 120) -> str:
        token = str(uuid.uuid4())
        self.pending_actions[token] = {
            "user_id": user_id,
            "action_type": action_type,
            "data": data or {},
            "expires_at": time.time() + timeout
        }
        return token

    def get(self, token: str):
        action = self.pending_actions.get(token)
        if action and action["expires_at"] > time.time():
            return action
        return None

    def consume(self, token: str):
        action = self.get(token)
        if action:
            del self.pending_actions[token]
        return action

confirmation_manager = ConfirmationManager()
