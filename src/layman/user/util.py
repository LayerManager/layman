
def get_user_profile(user_obj):
    if user_obj is None:
        result = {
            'authenticated': False,
            'friendly_name': 'Anonymous',
        }
    else:
        friendly_name = user_obj.get('name', None)
        workspace = user_obj.get('name', None)
        result = {
            'authenticated': True,
            'friendly_name': friendly_name,
            'workspace': workspace,
        }
    result = {k: v for k, v in result.items() if v is not None}
    return result