#encoding: utf-8
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import abort
import re
import pymongo
from pymongo import Connection
from time import time
app = Flask(__name__)

'''
Посмотреть потом

import re
regx = re.compile("^foo", re.IGNORECASE)
db.users.find_one({«files»: regx})

'''

class mongodb(object):
    from pymongo import MongoClient
    client = MongoClient()
    db = client['wow']
    items = db['items']
    users = db['users']
    servers = db['servers']

APP_PREFIX = '/wow/api/v1.0'
items_store = mongodb().items

@app.route("/hello")
@app.route("/hello/<name>")
def hello(name=None):
    if name is None:
        name = 'Mr.Nobody'
    return "<h>Hello, %s!</h>" % name

"""1
curl -D /dev/stdout http://localhost:5000/wow/api/v1.0/items/42
Получаем предмет по его id. Если не указак, то выдаем количество предметов,
у которых указан spell в itemSpells.
"""
@app.route(APP_PREFIX + '/items/<int:item_id>', methods = ['GET'])
@app.route(APP_PREFIX + '/items/', methods = ['GET'])
def get_item_by_id(item_id=None):
    """S. Finish"""
    start = time()
    item = items_store.find_one({'id': item_id}, {'_id': False}) if item_id else None
    if item:
        item['query_time'] = time() - start
        return jsonify(item)
    else:
        cnt = mongodb.db.items.find({'itemSpells.spellId': {'$exists': True}}).count()
        return jsonify({'items_with_spells': cnt})

"""2
curl -D /dev/stdout http://localhost:5000/wow/api/v1.0/items_batch/?batch=42-55
Выдаем предметы в интервале id'шников. При это предметы должны иметь отличную от 0
цену продажи и покупки. Сортируем по возрастанию цену покупки, по убыванию - цену продажи
"""
@app.route(APP_PREFIX + '/items_batch/', methods = ['GET'])
def get_item_by_batch():
    batch = request.args.get('batch', '0-10').split('-')  
    batch_min, batch_max = int(batch[0]), int(batch[1])
    items = items_store.find({'id': { '$gte': batch_min, '$lte': batch_max }, 'buyPrice' : { '$ne': 0 }, 'sellPrice' :\
        { '$ne': 0 } } , {'_id': False}).sort([ ('buyPrice', 1), ('sellPrice', -1) ])  # по возрастанию (1) и по убыванию (- 1)
    items = [i for i in items]
    if items:
        return jsonify({'items_batch': items})
    else:
        return jsonify({'error': 'Error'})
# Anton

"""3
curl -D /dev/stdout -H "Content-Type: application/json" -X POST -d '{"name":"Shadow book", "description": "the book of shadows"}' http://localhost:5000/wow/api/v1.0/items/
Добавляем новый предмет
"""
@app.route(APP_PREFIX + '/items/', methods = ['POST'])
def create_item():
    if not request.json or not 'name' in request.json:
        abort(400)
    item = {
        'id': items_store.count() + 1,
        'name': request.json['name'],
        'description': request.json.get('description', ""),
    }
    items = items_store.insert(item)
    return jsonify({'result': True})
# Anton 
"""4
curl -D /dev/stdout -H "Content-Type: application/json" -X PUT -d '{"name": "WhoreCleaner"}' http://localhost:5000/wow/api/v1.0/items/42
Обновляем предмет. Добавляем, если не существует
"""
@app.route(APP_PREFIX + '/items/<int:item_id>', methods = ['PUT'])
def update_item(item_id):
    """S. Finish"""
    item = items_store.find_one({'id': item_id}, {'_id': False})
    if not item:
        abort(404)
    if not request.json:
        abort(400)
    name = request.json.get('name', item['name'])
    description = request.json.get('description', item['description'])

    if item:
        mongodb.db.items.update({'id': item_id}, {'$set': {'name': name, 'description': description}})
    else:
        mongodb.db.items.insert({'id': item_id, 'name': name, 'description': description, '_id': False})

    return jsonify({'result': True})

"""5
curl -D /dev/stdout  -X DELETE  http://localhost:5000/wow/api/v1.0/items/42
Удаляем предмет
"""
@app.route(APP_PREFIX + '/items/<int:item_id>', methods = ['DELETE'])
def delete_item(item_id):
    item = items_store.find_one({'id': item_id}, {'_id': False})
    if not item:
        abort(404)
    items_store.remove({"id": item_id})
    return jsonify({'result': True})
#Anton
"""6
wget -qO- http://127.0.0.1:5000/wow/api/v1.0/weapons/?speed=1.0&damage=1-10&dps=1.0
Ищем предмет с указканным диапазоном урона, со скоростью больше указанной, с dps больше указанного.
"""
@app.route(APP_PREFIX + '/weapons/', methods = ['GET'])
def get_weapon():
    dps = request.args.get('dps', '0.0')
    speed = request.args.get('speed', '0.0')
    damage = request.args.get('damage', '0-0').split('-')  
    damage_min, damage_max = int(damage[0]), int(damage[1])

    items = items_store.find({"weaponInfo.damage.maxDamage": damage_max, "weaponInfo.damage.minDamage": damage_min , "weaponInfo.dps": { "$gt": dps }, "weaponInfo.weaponSpeed": { "$gt": speed }  }, {'_id': False});

    items = [i for i in items]
    if items:
        return jsonify({'items': items})
    else:
        return jsonify({'error': 'No such item'})

#Anton. Запрос вроде правильный, но возващает чуть больше, чем нефига
"""7
wget -qO- http://127.0.0.1:5000/wow/api/v1.0/items_w_spells/?level=8&buyPrice=0-111
Ищем предметы в указанном диапазоне buyPrice, при этом они должны иметь отличный от пустого
параметр itemSpells. Ну, и должны быть ниже указанного level
"""
@app.route(APP_PREFIX + '/items_w_spells/', methods = ['GET'])
def get_item_w_spells_by_price():
    '''S. Finish'''
    level = int(request.args.get('level', 80))
    prices = request.args.get('buyPrice', '0-10000').split('-')  
    price_min, price_max = int(prices[0]), int(prices[1])
    items = mongodb.db.items.find({'$and': [{"buyPrice": { '$gte': price_min, '$lte': price_max }},\
                                            {'itemLevel': {'$lte': level}}]}, {'itemSpells': {'$exists': True}})
    items = [i for i in items]
    if items:
        return jsonify({'items': items})
    else:
        return jsonify({'error': 'No such item'})

"""8
wget -qO- http://127.0.0.1:5000/wow/api/v1.0/armor/?armor=0&name_like=shadow
Ищем предметы, у которых baseArmor выше указанного, а имя подходит по шаблон name_like
"""
@app.route(APP_PREFIX + '/armor/', methods = ['GET'])
def get_armor():
    '''S. FIX ME'''
    name_like = request.args.get('name_like', 'death')
    armor = int(request.args.get('armor', '0'))
    '''
     OperationFailure: database error: Unsupported projection option: $regex
     в консоле работает, тут -- нет :(
    '''
    regx = re.compile(u"[\w]*"+name_like+u"[\w]*", re.IGNORECASE)
    items = mongodb.db.items.find({"baseArmor": {"$gt": armor}}, {'name': regx}, {'_id': False})
    items = [i for i in items]
    if items:
        return jsonify({'items': items})
    else:
        return jsonify({'error': 'No such item'})

#Anton and Sawa
"""
-------------------------------------------------------------------------------------------------------
1. Запустить users.py. Посмотреть, что вышло.
2. Поискать пользователей по индексу, посмотреть explain. Улучшить время путем создания индекса

mongodb.db.users.index_information()
mongodb.db.users.create_index('uid', 1)
3. Поискать пользователей по времени в игре,  посмотреть explain.
Улучшить время путем создания уникального индекса (с удалением дубликатов?)

mongodb.db.users.create_index('time_in_game', 1)
4. Через коллекцию users посчитать число пользователей на сервере N. 
Улучшить время путем создания многоключевого индекса.

??? servers
5.Найти сервера, где, например, популяция орды > N, а популяция альянса < M. 
Улучшить время путем создания составного индекса.
6. Удалить из половины серверов поле serial_number.
7. Поискать сервера по серийному номеру. Улучшить время путем создания уникального индекса (разряженного?).
8. Для коллекции servers посмотреть информацию о индексах, их общий размер и статистику коллекции. То же для users.
---------------------------------------------------------------------------------------------------------
1. Посчитать число серверов с каждым размером RAM
db.servers.group(
{
    key: {"tech.RAM": true}, 
    initial: {sum: 0}, 
    reduce: function(doc, prev) { prev.sum += 1}
});
2. Посчитать число серверов с каждым размером RAM и типом HDD. Отсортировать по RAM
3. Посчитать общую популяцию для серверов с каждым размером RAM и типом HDD. Отсортировать по размеру популяции
4. Посчитать общую популяцию для серверов с каждым размером RAM и типом HDD. Отсортировать по размеру популяции
5. Посчитать среднюю популяцию для серверов с каждым размером RAM и типом HDD. А затем, основываясь на предыдущих данных, среднюю популяцию для серверов  с каждым типом HDD. За один запрос
6. Найти максимальную, минимальную и среднюю цену покупки (buyPrice) в коллекции items 

"""

if __name__ == "__main__":
    app.debug = True
    app.run()
