from colombia import create_app

import sys

app = create_app()

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--gevent":
        # TODO: monkey patch should probably happen before everything else
        from gevent import monkey; monkey.patch_all()
        from gevent.wsgi import WSGIServer
        server = WSGIServer(("0.0.0.0",8001), application=app)
        server.serve_forever()
    else:
        app.run(host="0.0.0.0", port=app.config["PORT"])
