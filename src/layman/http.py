from flask import jsonify

def error(message, code=400):
    return jsonify({'message': message}), 400