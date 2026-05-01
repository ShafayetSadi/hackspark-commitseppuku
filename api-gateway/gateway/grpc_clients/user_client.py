import grpc
import grpc.aio

from shared.grpc_gen import user_pb2_grpc


def get_stub(addr: str) -> user_pb2_grpc.UserServiceStub:
    channel = grpc.aio.insecure_channel(addr)
    return user_pb2_grpc.UserServiceStub(channel)
