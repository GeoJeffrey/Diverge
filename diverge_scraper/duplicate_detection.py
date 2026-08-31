"""
duplicate_detection.py

Phase 4: Near-duplicate post detection using MinHash signatures (via datasketch).
For each (ticker, window):
  - Computes MinHash signature for each post's raw_text.
  - Compares pairwise; flags posts with >90% similarity (Jaccard > 0.90) to at least one other post
    from a DIFFERENT account (account_id_1 != account_id_2).
  - duplicate_ratio = (near_duplicate_posts_count) / (total_posts_in_window).
"""

from typing import Any, Dict, List, Optional

from datasketch import MinHash

from . import utils

logger = utils.setup_logger("duplicate_detection")


def get_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Compute MinHash signature for a text string using word shingles."""
    m = MinHash(num_perm=num_perm)
    words = text.lower().split()
    for w in words:
        m.update(w.encode("utf-8"))
    return m


def compute_duplicate_ratio(posts: List[Dict[str, Any]], similarity_threshold: float = 0.90) -> float:
    """
    Compute duplicate_ratio for a list of post dicts.
    Each dict must have: 'post_id', 'account_id', 'raw_text'.
    Returns float ratio in [0.0, 1.0].
    """
    total_posts = len(posts)
    if total_posts <= 1:
        return 0.0

    # Build MinHash signatures
    minhashes: List[Tuple[str, str, MinHash]] = []
    for p in posts:
        text = p.get("raw_text", "")
        if text:
            m = get_minhash(text)
            minhashes.append((p.get("post_id", ""), p.get("account_id", ""), m))

    if not minhashes:
        return 0.0

    duplicate_post_ids = set()

    for i in range(len(minhashes)):
        id_i, acc_i, mh_i = minhashes[i]
        for j in range(i + 1, len(minhashes)):
            id_j, acc_j, mh_j = minhashes[j]

            # Only flag as duplicate if posted by DIFFERENT accounts
            if acc_i and acc_j and acc_i != acc_j:
                sim = mh_i.jaccard(mh_j)
                if sim >= similarity_threshold:
                    duplicate_post_ids.add(id_i)
                    duplicate_post_ids.add(id_j)

    duplicate_ratio = round(len(duplicate_post_ids) / total_posts, 4)
    return duplicate_ratio
