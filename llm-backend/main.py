#!/usr/bin/env python3

import os
import time
import random
import logging
import pyroscope
from fastapi import FastAPI, Request
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import SpanKind, Status, StatusCode
from traceloop.sdk import Traceloop

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-llm-backend")

# Pyroscope setup
pyroscope.configure(
    application_name="mock-llm-backend",
    server_address=os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040"),
    enable_logging=False,
)

# Initialize Traceloop SDK (includes OTLP exporter setup)
Traceloop.init(
    app_name="mock-llm-backend",
    api_endpoint=os.getenv("OTLP_ENDPOINT", "alloy:4317")
)

# FastAPI app and OTEL setup
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

# Pydantic models for request validation
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int

@app.post("/v1/chat/completions")
async def mock_chat_completion(req: ChatRequest, request: Request):
    prompt = req.messages[-1].content
    logger.info(f"Received prompt: {prompt}")

    with tracer.start_as_current_span("generate_mock_response", kind=SpanKind.SERVER) as span:
        # Simulate latency
        latency = random.uniform(1, 5)
        time.sleep(latency)
        span.set_attribute("simulated.latency_seconds", latency)

        # Simulate failure (20%)
        if random.random() < 0.2:
            error_message = "Simulated LLM failure"
            logger.warning(f"Simulated failure: {error_message}")
            span.set_status(Status(StatusCode.ERROR, error_message))
            span.set_attribute("error", True)
            span.set_attribute("error.message", error_message)
            return {
                "error": {
                    "message": error_message,
                    "type": "mock_failure",
                    "code": 500
                }
            }

        # Construct mock response
        cleaned_prompt = prompt.strip().lower()
        reply = f"Echo: {cleaned_prompt[:100]}"

        span.set_status(Status(StatusCode.OK))
        span.set_attribute("mock.model", req.model)
        span.set_attribute("mock.input.length", len(cleaned_prompt))
        span.set_attribute("mock.reply.length", len(reply))
        span.set_attribute("llm.prompts", str(req.messages))

        logger.info(f"Responding with: {reply}")

        return {
            "id": "mockcmpl-xyz",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply,
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(cleaned_prompt) // 4,
                "completion_tokens": len(reply) // 4,
                "total_tokens": (len(cleaned_prompt) + len(reply)) // 4
            }
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting mock-llm-backend locally on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
