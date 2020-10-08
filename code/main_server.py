import os
from flask import Flask, jsonify, request
from flask import render_template
from flask import json
from datetime import datetime
import grpc
import pymongo
import time
from bson import ObjectId
import requests
import sgx_pb2
import sgx_pb2_grpc

app = Flask(__name__)

f = open('server.conf')
lines = f.readlines()
f.close()

uri = lines[0].strip()
database_str = lines[1].strip()
data_col_str = lines[2].strip()
deal_col_str = lines[3].strip()
mongo = pymongo.MongoClient(uri)
data_col = mongo[database_str][data_col_str]
deal_col = mongo[database_str][deal_col_str]

server_dir = os.path.dirname(__file__)
data_path = os.path.join(server_dir, "data.json")
order_path = os.path.join(server_dir, "order.json")
balance_path = os.path.join(server_dir, "balance.json")

service_id = 13321
HOSPITAL = ['BH1', 'BH2', 'BH3']
DEPARTMENT = ['Internal Medicine', 'Surgery']
DISEASE = ['Diabetes', 'Heart Disease']
GENDER = ['Male' ,'Female']
AGE_RANGE = ['<20', '20-30', '30-40', '40-50', '50-60', '60-70', '>70']
FUNCTION=['Distribution', 'SUM', 'Median', 'Linear Regression', 'SVM', 'Linear Model 1']


@app.route('/get_deals')
def getDeals():
    deal_list = deal_col.find({})
    res = []
    for item in deal_list:
        item['_id'] = str(item['_id'])
        #item['createdAt'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['createdAt']));
        res.append(item)
    return jsonify(res)


@app.route('/dashboard')
def dashBoard():
    return render_template('dashboard.html')

@app.route('/phone/<num>')
def phone(num):
    deal_list = deal_col.find()
    res = []
    for item in deal_list:
        item['_id'] = str(item['_id'])
        #item['createdAt'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['createdAt']));
        res.append(item)
    if int(num) > 0 and len(res) > int(num):
        return render_template('phone.html',deal_list=res, if_toast=1)
    else:
        return render_template('phone.html',deal_list=res, if_toast=0)

@app.route('/hospital/<num>')
def hospital(num):
    deal_list = deal_col.find()
    res = []
    for item in deal_list:
        item['_id'] = str(item['_id'])
        #item['createdAt'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['createdAt']));
        res.append(item)
    if int(num) > 0 and len(res) > int(num):
        return render_template('hospital.html',deal_list=res, if_toast=1)
    else:
        return render_template('hospital.html',deal_list=res, if_toast=0)

@app.route('/patient_operate')
def patientOperate():
    deal_id = request.args.get('deal')
    op_type = int(request.args.get('op')) + 1
    res = deal_col.find_one({'_id': ObjectId(deal_id)})
    if res['hospital_permit'] > 0 and op_type > 0:
        deal_col.update_one({'_id': ObjectId(deal_id)}, {'$set':{'patient_permit': op_type, 'exec_status': 1}})
    else:
        deal_col.update_one({'_id': ObjectId(deal_id)}, {'$set':{'patient_permit': op_type}})
    return 'ok'

@app.route('/hospital_operate')
def hospitalOperate():
    deal_id = request.args.get('deal')
    op_type = int(request.args.get('op')) + 1
    res = deal_col.find_one({'_id': ObjectId(deal_id)})
    #deal_col.update_one({'_id': ObjectId(deal_id)}, {'$set':{'hospital_permit': op_type}})
    if res['patient_permit'] > 0 and op_type > 0:
        deal_col.update_one({'_id': ObjectId(deal_id)}, {'$set':{'hospital_permit': op_type, 'exec_status': 1}})
    else:
        deal_col.update_one({'_id': ObjectId(deal_id)}, {'$set':{'hospital_permit': op_type}})
    return 'ok'


@app.route('/athena')
def athena():
    return render_template('athena.html')

@app.route('/athena-service')
def athena_service():
    return render_template('athena-service.html')

@app.route('/athena-order')
def athena_order():
        return render_template('athena-order.html')

@app.route('/athena-statistics')
def athena_statistics():
        return render_template('athena-statistics.html')

@app.route('/athena-balance')
def athena_balance():
        return render_template('athena-balance.html')

@app.route('/athena-login')
def athena_login():
        return render_template('athena-login.html')

@app.route('/athena-test')
def athena_test():
        return render_template('v-4.html')

@app.route('/api/order', methods=['GET'])
def getOrders():
    deal_list = deal_col.find()
    res = []
    for item in deal_list:
        res_item = {}
        res_item['service_id'] = str(item['service_id'])
        res_item['issue_time'] = item['issue_time']
        res_item['hospitals'] = [HOSPITAL[hos] for hos in item['hospitals']]
        res_item['record_num'] = [str(rec) for rec in item['record_num']]
        res_item['order_status'] = item['order_status']
        res_item['exec_status'] = item['exec_status']
        res_item['function'] = FUNCTION[item['func']]
        res_item['fixed_fee'] = str(item['fixed_fee'])
        res_item['security'] = item['security']
        res.append(res_item)

    return jsonify(res)


@app.route('/api/balance', methods=['GET'])
def getBalance():
    deal_list = deal_col.find({'balance_done': 0})
    res = []
    for item in deal_list:
        res_item = {}
        res_item['service_id'] = str(item['service_id'])
        res_item['issue_time'] = item['issue_time']
        res_item['hospitals'] = [HOSPITAL[hos] for hos in item['hospitals']]
        res_item['hospital_fee'] = [str(rec*0.5) for rec in item['record_num']]
        res_item['func_fee'] = str(item['func_fee'])
        exec_fee = int(item['exec_sec'] * 2/3)
        res_item['exec_fee'] = str(exec_fee)
        res_item['total_fee'] = str(item['fixed_fee'] + exec_fee + item['func_fee'])
        res.append(res_item)
    print(res)
    return jsonify(res)


@app.route('/api/data', methods=['POST'])
def getData():
    filter = request.get_json()
    print(filter)
    #add query builder
    data_query = {'$and':[{'hospital': {'$in': filter['hospital']},
                    'department': {'$in': filter['department']},
                    'disease': {'$in': filter['disease']},
                    'sex': {'$in': filter['gender']},
                    'age_range': {'$in': filter['age_range']}}]}
    #print(data_query)
    data_list = data_col.find(data_query)
    res = []
    for item in data_list:
        #print(item)
        res_item = {}
        res_item['hospital'] = HOSPITAL[item['hospital']]
        res_item['department'] = DEPARTMENT[item['department']]
        res_item['disease'] = DISEASE[item['disease']]
        res_item['gender'] = GENDER[item['sex']]
        res_item['age_range'] = AGE_RANGE[item['age_range']]
        res_item['hash'] = str(item['_id'])[-8:]
        res.append(res_item)

    return jsonify(res)

@app.route('/api/service', methods=['POST'])
def postService():
    global service_id
    service = request.get_json()
    dt_string = datetime.now()

    deal = {}
    deal['service_id'] = service_id
    service_id += 1
    deal['issue_time'] = dt_string.strftime("%Y-%m-%d %H:%M:%S")
    deal['exec_status'] = 2
    deal['exec_sec'] = 0
    deal['order_status'] = 1
    deal['hospitals'] = service['hospitals']
    deal['record_num'] = service['record_num']
    deal['func']=service['func']
    deal['fixed_fee']=service['fixed_fee']
    deal['security']=service['security']
    deal['record_total']=service['record_total']
    deal['func_fee']=service['func_fee']
    deal['balance_done'] = 1
    deal['result'] = {}
    deal['hospital_permit'] = 0
    deal['patient_permit'] = 0

    print(deal)

    deal_col.insert_one(deal)

    #authorization and update exec_status
    #deal_col.update_one({'service_id': service_id - 1}, {'$set': {'exec_status':1}})

    # if service['func'] == 0:
    #     result = {'type': 0}
    #     func_id = 1
    # if service['func'] == 3:
    #     result = {'type': 1}
    #     # 'params': [4.345,0.934,-2.061,1.672,1.145,11.537,88.984,-0.094]
    #     func_id = 2
    # if service['func'] == 5:
    #     result = {'type': 2}
    #     # 'predict': [74.135, 193.028, 129.666, 169.199, 75.297, 157.860], 'gt': [75.000, 166.000, 168.000, 85.000, 59.000, 276.000]
    #     func_id = 3
    #
    #
    # #execution
    # ok, exec_sec = call_func(func_id)
    # if ok == 0:
    #     print('Calling function' + FUNCTION[service['func']] + 'succeed!\n')
    #     res = {'$set': {'result': result}}
    #     deal_col.update({'service_id': service_id - 1}, {'$set': {'exec_status':0,
    #                         'order_status':0,
    #                         'balance_done':0,
    #                         'exec_sec': exec_sec,
    #                         'result': result}
    #                         })
    # else:
    #     print("calling function failed!\n")

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


def call_func(id):
    with grpc.insecure_channel('166.111.131.17:7666') as channel:
        stub = sgx_pb2_grpc.SecureFuncStub(channel)
        response = stub.SGXFunc(sgx_pb2.FuncId(value=id))
        print("Secure function executed: " + str(response.value))
    return 0, response.value

@app.route('/test',)
def testRpc():
    cur_url =  'http://172.16.1.129:8545'
    headers = {'content-type': 'application/json'}

    # Example echo method
    payload = {
        "method": "comfirmation",
        "params": ["0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45","0xf4128988cbe7df8315440adde412a8955f7f5ff9a5468a791433727f82717a6753bd7188207952 0x60320b8a71bc314404ef7d194ad8cac0bee1e331", "0xf4128988cbe7df8315440adde412a8955f7f5ff9a5468a791433727f82717a6753bd7188207952", "0x350dc2cd494ca089518a3e5a8773e5329c5c4a65", "0xd7dff5ff9a5fd71882a791433727f82717a670795241246853b8315440a8955f7de412a8988cbe"],
        "jsonrpc": "2.0",
        "id": 1,
    }
    response = requests.post(cur_url, data=json.dumps(payload), headers=headers).json()

    print(response)
    return 'ok'


if __name__ == '__main__':
    # clear deal table
    # count = deal_col.delete_many({})

    # connect with sgx machine
    app.run(debug=True)
