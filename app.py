from flask import Flask, jsonify, render_template, request
from flask.json.provider import JSONProvider
from bson import ObjectId
from pymongo import MongoClient
import socketio
from enum import Enum
import certifi
import json
from datetime import datetime, timezone


app = Flask(__name__)
sio = socketio.Server()

app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
# test DB를 위한 코드입니다
ca = certifi.where()
client = MongoClient('mongodb+srv://answldjs1836:ehVAtTGQ99erpdeX@cluster0.pceqwc3.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
###############################################
# todo: 서버에 올릴때 꼭 주석 제거 production용 DB
# client = MongoClient('localhost', 27017)


db = client.gikhub

class RequestStatus(Enum):
    IN_PROGRESS = "진행중"
    COMPLETED = "거래 완료"

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

app.json = CustomJSONProvider(app)


@app.route('/' , methods=['GET'])
def render_home():
    return render_template('index.html')

@app.route('/chatting' , methods=['GET'])
def render_chat_room():
    return render_template('chatting.html')


@app.route('/board', methods=['GET'])
def render_create_board():
    return render_template('create_board.html')


@app.route('/api/boards', methods=['GET'])
def list_boards():
    try:
        items = list(db.items.find(
            {'deletedAt': None}, {'title': 1, 'content': 1}))
        return jsonify(items)
    except Exception as e:
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500


@app.route('/api/boards/<item_id>', methods=['GET'])
def get_memo(item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return jsonify({'message': 'Invalid item ID'}), 400

        item = db.memos.find_one(
            {'_id': ObjectId(item_id), 'deletedAt': None}, {'title': 1, 'content': 1, 'likes': 1})

        if item is None:
            return jsonify({'message': 'Item not found'}), 404

        return jsonify(item)
    except Exception as e:
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500


@app.route('/api/boards', methods=['POST'])
def create_board():
    try:
        data = request.json

        if not data:
            return jsonify({"message": "No data provided"}), 400

        title = data.get('title')
        content = data.get('content')
        price=data.get('price')

        if not title:
            return jsonify({"message": "Missing 'title' in request"}), 400

        if not content:
            return jsonify({"message": "Missing 'content' in request"}), 400

        if not price:
            return jsonify({"message": "Missing 'price' in request"}), 400

        now = datetime.now(timezone.utc)
        status=RequestStatus.IN_PROGRESS.value
        # todo userId 토큰에서 얻은값으로 변경
        temporaryId="userId"

        result = db.items.insert_one(
            {
                'title': data['title'],
                'content': data['content'],
                'price': data['price'],
                # todo userId 토큰에서 얻은값을 ObjectId로 변경하여 저장
                'userId':temporaryId,
                'status': status,
                'createdAt': now,
                'updatedAt': now,
                'deletedAt': None,
            }
        )

        return jsonify({"_id": result.inserted_id}), 201
    except Exception as e:
        print(str(e))
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500


@app.route('/api/memos/<item_id>', methods=['PUT'])
def update_memo(item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return jsonify({'message': 'Invalid item ID'}), 400

        data = request.json

        if not data:
            return jsonify({"message": "No data provided"}), 400

        title = data.get('title')
        content = data.get('content')

        if not title:
            return jsonify({"message": "Missing 'title' in request"}), 400

        if not content:
            return jsonify({"message": "Missing 'content' in request"}), 400

        now = datetime.now(timezone.utc)

        result = db.memos.update_one({'_id': ObjectId(item_id), 'deletedAt': None}, {
            '$set': {
                'title': data["title"],
                'content': data["content"],
                'updatedAt': now,
            }
        })

        if result.matched_count == 0:
            return jsonify({"message": "Item not found"}), 404
        elif result.modified_count == 0:
            return jsonify({"message": "No changes made to the item"}), 200
        else:
            return jsonify({"message": "Item updated successfully"})
    except Exception as e:
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500


@app.route('/api/memos/<item_id>', methods=['DELETE'])
def delete_memo(item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return jsonify({'message': 'Invalid item ID'}), 400

        now = datetime.now(timezone.utc)

        result = db.memos.update_one({'_id': ObjectId(item_id), 'deletedAt': None}, {
            '$set': {
                'deletedAt': now,
            }
        })

        if result.matched_count == 0:
            return jsonify({"message": "Item not found"}), 404
        elif result.modified_count == 0:
            return jsonify({"message": "No changes made to the item"}), 200
        else:
            return jsonify({"message": "Item deleted successfully"})
    except Exception as e:
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500


@app.route('/api/memos/likes/<item_id>', methods=['PATCH'])
def like_memo(item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return jsonify({'message': 'Invalid item ID'}), 400

        now = datetime.now(timezone.utc)

        result = db.memos.update_one(
            {'_id': ObjectId(item_id), 'deletedAt': None}, {
                '$set': {
                    'updatedAt': now
                },
                '$inc': {
                    'likes': 1
                }
            })

        if result.matched_count == 0:
            return jsonify({"message": "Item not found"}), 404
        elif result.modified_count == 0:
            return jsonify({"message": "No changes made to the item"}), 200
        else:
            return jsonify({"message": "Item updated successfully"})
    except Exception as e:
        data = {
            "type": "error",
            "error_message": str(e),
        }
        return jsonify({'message': 'Server Error'}), 500

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
