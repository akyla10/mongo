from bson import Code
from pymongo import MongoClient

class mongodb(object):
    client = MongoClient()
    db = client['wow']
    items = db['items']
    users = db['users']
    servers = db['servers']
    mapper_users = Code('''
            function () {
                this.servers.forEach(function(z) {
                   emit(z, 1);
                });
            }
            ''')
    reducer_users = Code('''
                function (key, values) {
                    var total = 0;
                    for (var i = 0; i < values.length; i++) {
                      total += values[i];
                    }
                    return total;
                }
                ''')
    mapper_server = Code('''
            function () {
                this.servers.forEach(function(z) {
                   emit(z, 1);
                });
            }
            ''')
    reducer_server = Code('''
                function (key, values) {
                    var total = 0;
                    for (var i = 0; i < values.length; i++) {
                      total += values[i];
                    }
                    return total;
                }
                ''')




#result = mongodb.db.users.map_reduce(mongodb.mapper_users, mongodb.reducer_users, "myresults")
result = mongodb.db.servers.map_reduce(mongodb.mapper_server, mongodb.reducer_server, "myresults")
for doc in result.find():
    print doc