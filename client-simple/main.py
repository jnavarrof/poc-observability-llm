#!/usr/bin/env python3

import logging
import os
import time
import random
import pyroscope
import requests

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.propagate import inject

from otel import setup_tracing

logging.basicConfig(level=logging.INFO)

# Pyroscope setup
pyroscope.configure(
    application_name="simple.python.client",
    server_address=os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040"),
    enable_logging=False,
)

# Tracing setup
tracer = setup_tracing("simple.python.client")

# Endpoints
SERVER_BASE = os.getenv("SERVER_URL", "http://server:8000")
CALCULATE_URL = f"{SERVER_BASE}/calculate"
PING_URL = f"{SERVER_BASE}/ping"
TEST_OPENAI_URL = f"{SERVER_BASE}/test-openai"

def ping_server():
    with tracer.start_as_current_span("client_request.healthcheck_ping", kind=SpanKind.INTERNAL) as root_span:
        headers = {}
        inject(headers)
        try:
            response = requests.get(PING_URL, headers=headers)
            response.raise_for_status()
            logging.info(f"Ping response: {response.json()}")
            root_span.set_status(Status(StatusCode.OK))
        except Exception as e:
            logging.error(f"Healthcheck ping failed: {e}")
            root_span.set_status(Status(StatusCode.ERROR, str(e)))

def call_calculate(prompt_type: str):
    with tracer.start_as_current_span(f"client_request.call_{prompt_type}", kind=SpanKind.INTERNAL) as root_span:
        headers = {}
        inject(headers)
        with pyroscope.tag_wrapper({"function": prompt_type}):
            try:
                response = requests.get(CALCULATE_URL, params={"prompt": prompt_type}, headers=headers)
                response.raise_for_status()
                logging.info(f"{prompt_type} response: {response.json()}")
                root_span.set_status(Status(StatusCode.OK))
            except Exception as e:
                logging.error(f"Error calling calculate/{prompt_type}: {e}")
                root_span.set_status(Status(StatusCode.ERROR, str(e)))

def call_test_openai():
    with tracer.start_as_current_span("client_request.test_openai", kind=SpanKind.INTERNAL) as root_span:
        headers = {}
        inject(headers)
        try:
            response = requests.get(TEST_OPENAI_URL, headers=headers)
            response.raise_for_status()
            logging.info(f"Test OpenAI response: {response.json()}")
            root_span.set_status(Status(StatusCode.OK))
        except Exception as e:
            logging.error(f"Test OpenAI call failed: {e}")
            root_span.set_status(Status(StatusCode.ERROR, str(e)))

if __name__ == "__main__":
    while True:
        # ping_server()
        # time.sleep(2)

        # Choose one of the operations randomly
        random.choice([
            lambda: call_calculate("fast"),
            lambda: call_calculate("slow"),
            # call_test_openai
        ])()

        time.sleep(2)
