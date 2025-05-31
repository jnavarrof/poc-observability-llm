from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor


def setup_tracing(
    service_name: str,
    otlp_endpoint: str = "alloy:4317",
    instrument_requests: bool = True,
    instrument_fastapi: bool = False,
    instrument_openai: bool = False,
    fastapi_app=None,
):
    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: service_name})
    )
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)

    if instrument_requests:
        RequestsInstrumentor().instrument()

    if instrument_fastapi and fastapi_app:
        FastAPIInstrumentor.instrument_app(fastapi_app)

    if instrument_openai:
        OpenAIInstrumentor().instrument()

    return trace.get_tracer(service_name)
