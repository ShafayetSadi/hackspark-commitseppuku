import grpc
import grpc.aio

from shared.grpc_gen import rental_pb2_grpc


def get_stub(addr: str) -> rental_pb2_grpc.RentalServiceStub:
    channel = grpc.aio.insecure_channel(addr)
    return rental_pb2_grpc.RentalServiceStub(channel)
