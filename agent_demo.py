"""Simple Agent Layer demo for local testing."""
from planner import plan_shots


def main() -> None:
    prompt = (
        "A hero runs through a dark city alley, chased by a mysterious figure. "
        "He looks terrified and then turns to face his pursuer."
    )
    result = plan_shots(prompt, count=3)
    print("Parsed:")
    print(result["parsed"])
    print("\nShot Plan:")
    for shot in result["shots"]:
        print(shot)


if __name__ == "__main__":
    main()
