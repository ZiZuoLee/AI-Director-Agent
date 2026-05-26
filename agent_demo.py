"""Simple Agent Layer demo for local testing."""
from planner import plan_shots


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
