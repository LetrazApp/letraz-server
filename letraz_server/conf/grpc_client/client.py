import traceback
import grpc


class GRPCClient:
    def __init__(self, target: str, credentials=grpc.ssl_channel_credentials(root_certificates=None)):
        self.credentials = credentials
        self.target = target
        self.channel = None
        self.status = "UNINITIALIZED"
        self.exception = None

    def get_credentials(self):
        return self.credentials

    def set_credentials(self, credentials):
        self.credentials = credentials
        return self

    def connect(self):
        try:
            self.channel = grpc.secure_channel(target=self.target, credentials=self.credentials)
            print(grpc.channel_ready_future(self.channel).result(5))
            self.status = "OPERATIONAL"
        except Exception as ex:
            self.status = "FAILED"
            self.exception = traceback.format_exc()
        return self

    def disconnect(self):
        if self.channel:
            self.channel.close()
            self.channel = None
            self.status = "DISCONNECTED"

    def get_channel(self):
        return self.channel

    def get(self):
        return self.channel, self.status, self.exception

    def get_exception(self):
        return self.exception