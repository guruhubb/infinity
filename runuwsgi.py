from infinity import app
import logging

app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
