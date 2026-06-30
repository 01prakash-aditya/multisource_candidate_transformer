def calculate_confidence(source_types: list, is_stale: bool = False) -> float:
    """
    Calculate confidence based on source agreement, base source reliability, and staleness.
    """
    if not source_types:
        return 0.0

    # Base scores for each source type
    BASE_SCORES = {
        "ats_json": 0.9,
        "github": 0.8,
        "resume": 0.8,
        "csv": 0.7,
        "notes": 0.6
    }

    # Find the maximum base score among the sources that provided this field
    base_score = max((BASE_SCORES.get(s, 0.5) for s in source_types), default=0.5)
    
    # Agreement bonus: +0.15 if 2 or more sources agree
    agreement_bonus = 0.15 if len(set(source_types)) >= 2 else 0.0
    
    # Staleness penalty: simple -0.1 if marked stale
    staleness_penalty = 0.1 if is_stale else 0.0
    
    confidence = base_score + agreement_bonus - staleness_penalty
    
    # Cap at 1.0 and floor at 0.0
    return max(0.0, min(1.0, confidence))
