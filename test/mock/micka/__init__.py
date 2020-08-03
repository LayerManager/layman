def run(env_vars, app_config, host, port, debug, load_dotenv, options):
    import os
    # os.makedirs("/code/tmp/mock/micka-out", exist_ok=True)
    # sys.stdout = open(f"/code/tmp/mock/micka-out/{str(os.getpid())}.out", "w")
    # sys.stderr = open(f"/code/tmp/mock/micka-out/{str(os.getpid())}.err", "w")
    for k, v in env_vars.items():
        os.environ[k] = v

    from .app import create_app
    app = create_app(app_config)
    app.run(host, port, debug, load_dotenv, **options)
