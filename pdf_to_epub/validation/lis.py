from typing import List
import bisect

def calculate_lis_length(sequence: List[int]) -> int:
    """
    Calculates the length of the Longest Increasing Subsequence (LIS) 
    using binary search (Patience Sorting approach).
    Time Complexity: O(N log N)
    
    Args:
        sequence: A list of integers (positions).
        
    Returns:
        The length of the longest strictly increasing subsequence.
    """
    if not sequence:
        return 0
    
    # specialized list to store the smallest tail of all increasing subsequences
    # of length i+1 in tails[i]
    tails: List[int] = []
    
    for x in sequence:
        # Find the first element in tails that is >= x
        idx = bisect.bisect_left(tails, x)
        
        if idx < len(tails):
            tails[idx] = x
        else:
            tails.append(x)
            
    return len(tails)
