from bson import Code
from pymongo import MongoClient

class mongodb(object):
    client = MongoClient()
    db = client['wow']
    items = db['items']
    users = db['users']
    servers = db['servers']
    mapper = Code('''
            function () {
                this.servers.forEach(function(z) {
                   emit(z, 1);
                });
            }
            ''')
    reducecer = Code('''
                function (key, values) {
                    var total = 0;
                    for (var i = 0; i < values.length; i++) {
                      total += values[i];
                    }
                    return total;
                }
                ''')


result = mongodb.db.users.map_reduce(mongodb.mapper, mongodb.reducecer, "myresults")
for doc in result.find():
    print doc