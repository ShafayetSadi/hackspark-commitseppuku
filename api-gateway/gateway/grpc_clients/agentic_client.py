import grpc
import grpc.aio

from shared.grpc_gen import agentic_pb2_grpc


def get_stub(addr: str) -> agentic_pb2_grpc.AgenticServiceStub:
    channel = grpc.aio.insecure_channel(addr)
    return agentic_pb2_grpc.AgenticServiceStub(channel)
