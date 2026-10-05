import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=os.getenv("AGENT_HOST", "0.0.0.0"),
        port=int(os.getenv("AGENT_PORT", "8787")),
    )
