import os
import signal
from concurrent import futures

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import grpc
from app.authentication.services.auth_service import AuthService
from app.generated import auth_pb2_grpc
from django.conf import settings


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    server.add_insecure_port(f"{settings.HOST}:{settings.PORT}")
    server.start()
    print("🚀 gRPC server running on:", f"{settings.HOST}:{settings.PORT}")

    def handle_shutdown(signum, frame):
        print("🛑 Shutting down gRPC server...")
        server.stop(grace=5)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
