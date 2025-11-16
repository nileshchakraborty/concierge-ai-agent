"""Terminal CLI that runs the concierge agent using the project's DI wiring.

This script provides a thin wrapper around the existing `ConciergeAgentService`.
Run it with the workspace venv activated:

    python -m concierge.scripts.multimodal_cli

It supports passing a file path (image) as input; the image will be encoded and
included in the Ollama call when available.
"""
import asyncio
import os
from concierge.service.di import get_concierge_service


def main():
    svc = get_concierge_service()

    print("🤖 Local Concierge (multimodal CLI)")
    print('Type "quit" or "exit" to end the session.')
    history = []

    while True:
        user_input = input("What would you like to find? (or drop an image path)\n> ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            return

        if os.path.isfile(user_input):
            # pass image path via the history/goal string — the service can decide how to use it
            goal = f"Find information about the image at: {user_input}"
            # the service will call adapters and can use ollama_adapter.encode_image if needed
        else:
            goal = user_input

        try:
            summary = asyncio.run(svc.run_concierge_agent(goal, history))
            # If the service returns a dict with an `error` key, surface guidance
            if isinstance(summary, dict) and summary.get("error"):
                print("\n--- Concierge Error ---\n")
                print(summary.get("error"))
                print("\n-- Troubleshooting --\n")
                print("* Ensure Ollama is running at OLLAMA_HOST and that the model name is correct.")
                print("* Verify the Ollama server supports POST /api/generate and that the model is loaded.")
                print("* Set environment variables OLLAMA_HOST and OLLAMA_MODEL as needed.")
                print("\n")
            else:
                print("\n--- Summary ---\n")
                print(summary)
                print("\n---------------\n")
                history.append(f"User: {goal}")
                history.append(f"Agent: {summary}")
        except Exception as e:
            print(f"Error running concierge agent: {e}")


if __name__ == "__main__":
    main()
