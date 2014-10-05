from infinity import app
from flup.server.fcgi import WSGIServer
import logging

app.logger.setLevel(logging.DEBUG)
srv = WSGIServer(app, bindAddress=("127.0.0.1", 7080), multiprocess=True)

if __name__ == "__main__":
    srv.run()
