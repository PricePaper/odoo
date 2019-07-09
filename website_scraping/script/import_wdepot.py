
import xmlrpclib
import ssl
import csv


uname="admin"
pwd="confianzpricepaper"
db="price_db"

#socket = xmlrpclib.ServerProxy('https://odoodemo.pricepaper.com/xmlrpc/object',context=ssl._create_unverified_context())

socket = xmlrpclib.ServerProxy('http://10.254.101.44:8070/xmlrpc/object',context=ssl._create_unverified_context())

input_file = csv.DictReader(open("webstuarant.csv"))



products = socket.execute(db, 1, pwd, 'product.product', 'search_read', [], ['id','default_code'])
items = {product['default_code']: product['id'] for product in products}

count = 0
with open("ERROR.csv", "wb") as f, open("no_product.csv", "wb") as f1:

    for line in input_file:
        if line['URL']:
            continue
        if line['PPT CODE'] not in items:
            count+=1
            f1.write(line['PPT CODE'])
            f1.write('\n')
            print line['PPT CODE']
            continue
        vals={'product_id': items.get(line['PPT CODE']),
              'competitor_sku': line['WEBSTAURANT CODE'],
            #   'competitor_desc': line['DEPOT DESC'],
              'qty_in_uom': line['COUNT'],
              'web_config': 2
              }
        print vals
        status = socket.execute(db, 1, pwd, 'product.sku.reference', 'create', vals)
        print status
print count
