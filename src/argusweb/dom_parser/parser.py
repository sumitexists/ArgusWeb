

async def snapshot_parser(snapshot : str):
    clean = []
    lines = snapshot.splitlines()
    for line in lines:
        line = line.rstrip()
        if line.endswith(":") or ("/url:" in line.split()):
            continue
        clean.append(line)

    lines = "\n".join(clean)
    lines = [line.rstrip() for line in lines.splitlines() if line.strip()]

    line_depths = [len(line) - len(line.lstrip(' ')) for line in lines]
    if not line_depths:
        return []
    max_depth = max(line_depths)

    chunk_indent = [i for i in range(0, max_depth, 2)]

    num_levels = len(chunk_indent)
    chunks_by_level = [[] for _ in range(num_levels)]
    current_chunks = [[] for _ in range(num_levels)]

    for line, depth in zip(lines, line_depths):
        line = line.rstrip()
        for i, threshold in enumerate(chunk_indent):
            if depth <= threshold and current_chunks[i]:
                if len(current_chunks[i]) > 3 and len(current_chunks[i]) < 150:
                    chunks_by_level[i].append("\n".join(current_chunks[i]))
                    current_chunks[i] = []
                
            current_chunks[i].append(line)

    for i in range(num_levels):
        if current_chunks[i]:
            if len(current_chunks[i]) > 3 and len(current_chunks[i]) < 200:
                chunks_by_level[i].append("\n".join(current_chunks[i]))

    chunks = [chunk for chunks in chunks_by_level for chunk in chunks]
    return chunks

            
