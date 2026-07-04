"""
KOVIRX Endpoint Agent — Payload Compression.

gzip compression for telemetry payloads before network transmission.
Reduces bandwidth by 60-80% for typical JSON telemetry batches.
"""

import gzip
import json
import logging

logger = logging.getLogger("kovirx.agent.compression")


def compress_payload(data: dict, threshold: int = 1024) -> tuple[bytes, bool]:
    """
    Compress a JSON-serializable dict payload using gzip.

    Args:
        data: Dictionary to serialize and compress
        threshold: Minimum raw size in bytes to trigger compression

    Returns:
        Tuple of (payload_bytes, is_compressed)
    """
    raw = json.dumps(data, default=str).encode("utf-8")

    if len(raw) < threshold:
        return raw, False

    try:
        compressed = gzip.compress(raw, compresslevel=6)
        ratio = len(compressed) / len(raw) * 100
        logger.debug(
            "Compressed payload: %d → %d bytes (%.1f%%)",
            len(raw), len(compressed), ratio,
        )
        return compressed, True
    except Exception as e:
        logger.warning("Compression failed, sending uncompressed: %s", e)
        return raw, False


def decompress_payload(data: bytes) -> dict:
    """Decompress a gzipped JSON payload."""
    try:
        raw = gzip.decompress(data)
        return json.loads(raw)
    except Exception as e:
        logger.error("Decompression failed: %s", e)
        raise
