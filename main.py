
from fastapi import FastAPI
from uvicorn import run

from concierge.controller.concierge_agent_controller import ConciergeAgentController

app = FastAPI()
from concierge import main as conceirge

def main():
    conceirge.main()


if __name__ == "__main__":
    main()

