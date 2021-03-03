from layman import upgrade, app


if __name__ == '__main__':
    print(f'Starting standalone upgrade')
    with app.app_context():
        upgrade.upgrade()
    print(f'Standalone upgrade done')
