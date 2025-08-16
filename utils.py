import tiktoken

def count_tokens(text, model="gpt-4"):
    if not text:
        return 0
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_tokens_per_tc(model="gpt-4"):
    # Adjust based on model verbosity
    if "claude" in model:
        return 180
    else:
        return 150
