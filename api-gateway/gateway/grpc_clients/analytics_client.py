import grpc
import grpc.aio

from shared.grpc_gen import analytics_pb2_grpc


def get_stub(addr: str) -> analytics_pb2_grpc.AnalyticsServiceStub:
    channel = grpc.aio.insecure_channel(addr)
    return analytics_pb2_grpc.AnalyticsServiceStub(channel)
