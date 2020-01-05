from settings import create_app
import os
app = create_app()
if __name__ == '__main__':
    dev_host = os.getenv('DEV_HOST')
    if dev_host:
        app.run(host=dev_host, port=80)
    else:
        app.run()
