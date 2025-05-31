#!/usr/bin/env python3

import os
import requests
import pyroscope
from fastapi import FastAPI, Query
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.propagate import inject

from otel import setup_tracing

# Load environment variables
load_dotenv()

# Pyroscope setup
pyroscope.configure(
    application_name="simple.python.server",
    server_address=os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040"),
    enable_logging=False,
)

# FastAPI app and OTEL tracing setup
app = FastAPI()
tracer = setup_tracing(
    service_name="server-api",
    otlp_endpoint=os.getenv("OTLP_ENDPOINT", "alloy:4317"),
    instrument_requests=True,
    instrument_fastapi=True,
    instrument_openai=True,
    fastapi_app=app,
)

# OpenAI client
client = OpenAI()
MOCK_LLM_URL = os.getenv("MOCK_LLM_URL", "http://llm-backend:8000/v1/chat/completions")

@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@app.get("/ping")
def ping():
    with tracer.start_as_current_span("ping_handler", kind=SpanKind.SERVER) as span:
        span.set_status(Status(StatusCode.OK))
        return {"message": "pong"}


@app.get("/calculate")
def calculate(prompt: str = Query(...)):
    with tracer.start_as_current_span("process_prompt", kind=SpanKind.SERVER) as root_span:
        headers = {}
        inject(headers)

        try:
            # Step 1: Call mock LLM
            llm_payload = {
                "model": "mock-model",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
            }

            with tracer.start_as_current_span("call_mock_llm", kind=SpanKind.CLIENT) as llm_span:
                llm_span.set_attribute("http.method", "POST")
                llm_span.set_attribute("http.url", MOCK_LLM_URL)
                llm_span.set_attribute("peer.service", "mock-llm-backend")

                llm_resp = requests.post(MOCK_LLM_URL, json=llm_payload, headers=headers)
                llm_resp.raise_for_status()
                enriched_prompt = llm_resp.json()["choices"][0]["message"]["content"]
                llm_span.set_status(Status(StatusCode.OK))

            # Step 2: Use enriched prompt with OpenAI
            with tracer.start_as_current_span("call_openai_chat", kind=SpanKind.CLIENT) as ai_span:
                ai_span.set_attribute("http.method", "POST")
                ai_span.set_attribute("peer.service", "openai")
                ai_span.set_attribute("net.peer.name", "api.openai.com")

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": enriched_prompt}],
                    max_tokens=1,
                )

                ai_span.set_status(Status(StatusCode.OK))
                root_span.set_status(Status(StatusCode.OK))

            return {
                "original_prompt": prompt,
                "enriched_prompt": enriched_prompt,
                "response": response.choices[0].message["content"]
            }

        except Exception as e:
            root_span.set_status(Status(StatusCode.ERROR, str(e)))
            return {"error": str(e)}


@app.get("/test-openai")
def test_openai():
    with tracer.start_as_current_span("test_sync_openai_call", kind=SpanKind.SERVER) as root_span:
        try:
            with tracer.start_as_current_span("call_openai_chat", kind=SpanKind.CLIENT) as span:
                span.set_attribute("peer.service", "openai")
                span.set_attribute("net.peer.name", "api.openai.com")

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say hello"}],
                    max_tokens=1,
                )

                span.set_status(Status(StatusCode.OK))
                root_span.set_status(Status(StatusCode.OK))
                return {"status": "ok"}

        except OpenAIError as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            root_span.set_status(Status(StatusCode.ERROR, str(e)))
            return {"error": f"OpenAI API failed: {str(e)}"}


# Entrypoint for local dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
