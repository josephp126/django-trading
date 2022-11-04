from .server import Server


if __name__ == "__main__":

    try:

        server = Server()

        server.start()

    except KeyboardInterrupt:

        pass
