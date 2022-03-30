import xmlrpclib
import json
import time
import logging

__logger = logging.getLogger(__name__)

start_time = time.time()

database = '13_test_app'
login = 'admin'
password = '1'
url = 'http://localhost:8069'


common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(database, login, password, {})

models = xmlrpclib.ServerProxy(url + '/xmlrpc/object')

with open("img.png", "rb") as f:
    data = f.read()
    for i in range(0, 1000000):
        vals = {
            'list_price': i,
            'description': u'description',
            'available_in_pos': True,
            'display_name': 'Product_%s' % str(i),
            'name': 'Product_%s' % str(i),
            'to_weight': u'True',
        }
        models.execute_kw(database, uid, password, 'product.product', 'create', [vals])
        print i
