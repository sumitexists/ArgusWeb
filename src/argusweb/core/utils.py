
from argusweb.tools import get_snapshot
import difflib
import asyncio


def diff_generator(before_snapshot : str, after_snapshot: str) -> list:
    lines1 = before_snapshot.splitlines()
    lines2 = after_snapshot.splitlines()
    changes_only = [
        line
        for line in difflib.unified_diff(lines1, lines2, n=0, lineterm="")
        if not line.startswith(("---", "+++", "@@"))
    ]
    return changes_only

async def execution_eval(before_snapshot : str) -> dict:
    after_snapshot = await get_snapshot()

    changes_only = await asyncio.to_thread(diff_generator, before_snapshot, after_snapshot)

    return {
        "diff" :"\n".join(changes_only) if changes_only else "No differnce found"
    }
