"""
Formatting utilities for the Spotify Music Recommendation System
"""

def format_duration(ms: int) -> str:
    """Format milliseconds into MM:SS format"""
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def get_key_name(key: int) -> str:
    """Convert key number to musical key name"""
    keys = {
        0: 'C', 1: 'C# / Db', 2: 'D', 3: 'D# / Eb',
        4: 'E', 5: 'F', 6: 'F# / Gb', 7: 'G',
        8: 'G# / Ab', 9: 'A', 10: 'A# / Bb', 11: 'B'
    }
    return keys.get(key, 'Unknown')

def get_mode_name(mode: int) -> str:
    """Convert mode number to musical mode name"""
    return 'Major' if mode == 1 else 'Minor' 