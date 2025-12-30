from claude_skill.validation.completeness_checker import CompletenessChecker
from claude_skill.core.text_segmenter import segment_text, normalize_whitespace

def debug():
    source = "ALPHA. BETA. GAMMA. DELTA. EPSILON. ZETA. ETA. THETA. IOTA. KAPPA."
    target = "ALPHA. BETA. GAMMA. DELTA. ZETA. ETA. THETA. IOTA. KAPPA." # Missing EPSILON
    
    print("\n--- DEBUG START ---")
    
    # 1. Normalize
    norm_source = normalize_whitespace(source)
    norm_target = normalize_whitespace(target)
    print(f"Normalized Source: '{norm_source}'")
    print(f"Normalized Target: '{norm_target}'")
    
    # 2. Segment
    chunk_size = 10
    overlap = 0
    chunks = segment_text(source, chunk_size=chunk_size, overlap=overlap)
    print(f"\nGenerated {len(chunks)} chunks (Size={chunk_size}, Overlap={overlap}):")
    
    # 3. Search Loop Simulation
    current_pos = 0
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: '{chunk.text}'")
        
        # Search strategy from CompletenessChecker
        idx = norm_target.find(chunk.text, current_pos)
        found_method = "Optimized"
        
        if idx == -1:
            idx = norm_target.find(chunk.text)
            found_method = "Fallback"
            
        if idx != -1:
            print(f"  -> FOUND at index {idx} ({found_method})")
            current_pos = idx + len(chunk.text)
        else:
            print(f"  -> NOT FOUND! (Critical failure expected here)")

    # 4. Run Checker
    checker = CompletenessChecker(source, target, min_significant_len=5)
    result = checker.check(chunk_size=chunk_size, overlap=overlap)
    print(f"\nChecker Result: Valid={result.is_valid}, Score={result.completeness_score}")

if __name__ == "__main__":
    debug()
