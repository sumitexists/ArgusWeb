

def snapshot_parser(snapshot : str) -> str:
    clean = []
    lines = snapshot.splitlines()
    for line in lines:
        line = line.rstrip()
        if line.endswith(":") or ("/url:" in line.split()):
            continue
        clean.append(line)

    lines = "\n".join(clean)
    return lines
