"""Simple Agent Layer demo for local testing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.agent.planner import plan_shots


def main() -> None:
    prompt = (
        "主角在黑暗的城市小巷中奔跑，被神秘身影追赶。"
        "他满脸惊恐，然后转身面对追击者。"
    )
    result = plan_shots(prompt, count=3)
    print("Parsed:")
    print(result["parsed"])
    print("\nShot Plan:")
    for shot in result["shots"]:
        print(shot)


if __name__ == "__main__":
    main()
