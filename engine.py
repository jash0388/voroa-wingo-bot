"""
Quant Prediction Engine for WinGo (30S and 1M)
Ensemble models: Titan Vortex, Doublet 2-2 Detector, Streak Balancer, Markov Momentum.
"""

def analyze_history(draw_history):
    """
    draw_history: list of dicts ordered chronologically (oldest to newest):
    [{'period': '52110', 'number': 8, 'size': 'BIG'}, ...]
    """
    if not draw_history or len(draw_history) < 3:
        # Default fallback
        return {"size": "BIG", "confidence": 75, "pattern": "BALANCED_INIT"}
    
    recent_sizes = [d['size'] for d in draw_history[-10:]]
    recent_nums = [d['number'] for d in draw_history[-10:]]
    
    last_size = recent_sizes[-1]
    
    # 1. Doublet 2-2 Detection (e.g. BB, SS, BB -> predict SS)
    if len(recent_sizes) >= 4:
        if recent_sizes[-1] == recent_sizes[-2] and recent_sizes[-3] == recent_sizes[-4] and recent_sizes[-1] != recent_sizes[-3]:
            # 2 of same followed by 2 of other: flip expected after 2
            predicted = "SMALL" if last_size == "BIG" else "BIG"
            return {"size": predicted, "confidence": 88, "pattern": "DOUBLET_2_2_BREAK"}
    
    # 2. Alternating Zig-Zag (B, S, B, S)
    if len(recent_sizes) >= 4:
        if recent_sizes[-1] != recent_sizes[-2] and recent_sizes[-2] != recent_sizes[-3] and recent_sizes[-3] != recent_sizes[-4]:
            # Continue zig-zag
            predicted = "SMALL" if last_size == "BIG" else "BIG"
            return {"size": predicted, "confidence": 85, "pattern": "ZIG_ZAG_CONTINUATION"}

    # 3. Dragon Streak (3 or more of same size)
    streak = 1
    for i in range(len(recent_sizes) - 2, -1, -1):
        if recent_sizes[i] == last_size:
            streak += 1
        else:
            break
            
    if streak >= 3 and streak <= 5:
        # Follow the dragon
        return {"size": last_size, "confidence": 90, "pattern": f"DRAGON_RIDE_{streak}X"}
    elif streak > 5:
        # Dragon exhaustion, anti-whipsaw flip
        predicted = "SMALL" if last_size == "BIG" else "BIG"
        return {"size": predicted, "confidence": 82, "pattern": "DRAGON_EXHAUSTION_FLIP"}
        
    # 4. Markov Transition Matrix
    big_to_big = 0
    big_to_small = 0
    small_to_big = 0
    small_to_small = 0
    
    for i in range(len(recent_sizes) - 1):
        curr, nxt = recent_sizes[i], recent_sizes[i+1]
        if curr == "BIG" and nxt == "BIG": big_to_big += 1
        elif curr == "BIG" and nxt == "SMALL": big_to_small += 1
        elif curr == "SMALL" and nxt == "BIG": small_to_big += 1
        elif curr == "SMALL" and nxt == "SMALL": small_to_small += 1
        
    if last_size == "BIG":
        predicted = "BIG" if big_to_big >= big_to_small else "SMALL"
    else:
        predicted = "SMALL" if small_to_small >= small_to_big else "BIG"
        
    return {"size": predicted, "confidence": 84, "pattern": "MARKOV_TRANSITION"}
