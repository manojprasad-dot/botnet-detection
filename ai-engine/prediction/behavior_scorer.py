"""
KOVIRX AI Engine — Behavior Scorer.

Computes behavior-aware scores for the multi-source risk engine.
Takes raw flow features + behavior analysis results and produces
a normalized behavior_score for risk aggregation.
"""

import logging
import math
from collections import Counter

logger = logging.getLogger("kovirx.ai.behavior_scorer")


class BehaviorScorer:
    """
    Behavior score calculator for the multi-source risk engine.

    Analyzes flow features for behavioral indicators:
        - DNS regularity / DGA patterns
        - Connection interval regularity (beaconing)
        - Data transfer asymmetry (exfiltration)
        - Port scan indicators
        - Long-lived encrypted sessions
    """

    # Weight each behavior type
    WEIGHTS = {
        "dns_abuse": 0.25,
        "beaconing": 0.25,
        "exfiltration": 0.20,
        "scanning": 0.15,
        "encrypted_session": 0.15,
    }

    def score(self, features: dict[str, float], behavior_signals: list[dict] | None = None) -> dict:
        """
        Compute behavior score from flow features and optional behavior signals.

        Args:
            features: Feature vector dict from ML feature extractor
            behavior_signals: Optional pre-computed behavior analysis results

        Returns:
            Dict with behavior_score, behavior_type, and per-signal breakdown
        """
        scores: dict[str, float] = {}

        # DNS Abuse: high-entropy queries, DGA patterns
        dns_entropy = features.get("max_dns_entropy", 0.0)
        dns_query_count = features.get("dns_query_count", 0.0)
        if dns_entropy >= 4.0 and dns_query_count >= 3:
            scores["dns_abuse"] = min(1.0, (dns_entropy - 3.5) / 1.5)
        elif dns_entropy >= 3.5:
            scores["dns_abuse"] = min(0.5, (dns_entropy - 3.0) / 2.0)
        else:
            scores["dns_abuse"] = 0.0

        # Beaconing: regular connection intervals
        beacon_score = features.get("beacon_interval_score", 0.0)
        scores["beaconing"] = min(1.0, beacon_score)

        # Data Exfiltration: high outbound ratio
        bytes_sent = features.get("bytes_sent", 0.0)
        bytes_recv = features.get("bytes_recv", 0.0)
        if bytes_recv > 0 and bytes_sent / bytes_recv > 10:
            scores["exfiltration"] = min(1.0, (bytes_sent / bytes_recv) / 50.0)
        else:
            scores["exfiltration"] = 0.0

        # Port Scanning: high failed connection ratio
        failed_ratio = features.get("failed_connection_ratio", 0.0)
        tcp_flag_score = features.get("tcp_flag_score", 0.0)
        scores["scanning"] = min(1.0, (failed_ratio + tcp_flag_score) / 2.0)

        # Long-lived Encrypted Session proxy
        flow_duration = features.get("flow_duration", 0.0)
        packet_rate = features.get("packet_rate", 0.0)
        if flow_duration > 1800 and packet_rate < 0.1:
            scores["encrypted_session"] = min(1.0, flow_duration / 7200.0)
        else:
            scores["encrypted_session"] = 0.0

        # Incorporate pre-computed behavior signals if provided
        if behavior_signals:
            for signal in behavior_signals:
                sig_type = signal.get("pattern_type", "")
                sig_conf = signal.get("confidence", 0.0)
                if sig_type in scores:
                    scores[sig_type] = max(scores[sig_type], sig_conf)

        # Weighted aggregate
        weighted_sum = sum(
            scores.get(key, 0.0) * weight
            for key, weight in self.WEIGHTS.items()
        )
        behavior_score = min(1.0, weighted_sum)

        # Determine dominant behavior type
        if scores:
            dominant = max(scores, key=scores.get)
            behavior_type = dominant if scores[dominant] >= 0.3 else "normal"
        else:
            behavior_type = "normal"

        return {
            "behavior_score": round(behavior_score, 4),
            "behavior_type": behavior_type,
            "signal_breakdown": {k: round(v, 4) for k, v in scores.items()},
        }


# Module-level instance
behavior_scorer = BehaviorScorer()
