from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from runtime.state_schema import DispositionalState


class LocalEncryptedStateStore:
    """Local reference store, not production cryptography."""

    def __init__(self, key: str) -> None:
        self.key = key.encode("utf-8")
        self.records: dict[str, str] = {}

    def save(self, user_id: str, state: DispositionalState) -> dict[str, Any]:
        payload = json.dumps(state.to_dict(), sort_keys=True)
        encrypted = self._xor(payload.encode("utf-8"))
        self.records[user_id] = base64.b64encode(encrypted).decode("ascii")
        return {
            "user_id": user_id,
            "local_offline_encryption": True,
            "production_crypto": False,
            "scheme": "xor_sha256_stream_reference",
            "bytes": len(encrypted),
        }

    def export(self, user_id: str) -> dict[str, Any]:
        encrypted = self.records.get(user_id)
        if encrypted is None:
            return {"user_id": user_id, "found": False}
        decrypted = self._xor(base64.b64decode(encrypted.encode("ascii"))).decode("utf-8")
        return {
            "user_id": user_id,
            "found": True,
            "state": json.loads(decrypted),
        }

    def delete(self, user_id: str) -> dict[str, Any]:
        existed = user_id in self.records
        self.records.pop(user_id, None)
        return {"user_id": user_id, "deleted": existed}

    def _xor(self, payload: bytes) -> bytes:
        stream = bytearray()
        counter = 0
        while len(stream) < len(payload):
            block = hashlib.sha256(self.key + counter.to_bytes(8, "big")).digest()
            stream.extend(block)
            counter += 1
        return bytes(byte ^ stream[index] for index, byte in enumerate(payload))
