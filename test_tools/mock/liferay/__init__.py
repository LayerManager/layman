def run(env_vars, app_config, host, port, debug, load_dotenv, options):
    import os
    # import sys
    # os.makedirs("/code/tmp/mock-out", exist_ok=True)
    # sys.stdout = open(f"/code/tmp/mock-out/{str(os.getpid())}.out", "w")
    # sys.stderr = open(f"/code/tmp/mock-out/{str(os.getpid())}.err", "w")
    for key, value in env_vars.items():
        os.environ[key] = value

    from .app import create_app
    app = create_app(app_config)
    app.run(host, port, debug, load_dotenv, **options)
