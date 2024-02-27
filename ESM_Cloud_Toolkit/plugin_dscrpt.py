# basic
import os
import pickle
import numpy as np
import random
import string
import datetime
import shutil

# plugin
import re
import requests
from fastapi import FastAPI, Request

# file processing
import zipfile

# dscriptors
from dscribe.descriptors import SOAP

app = FastAPI()

dscrpt_options = ['None', 'SOAP']

def gen_uid():
    uid = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    uid.upper()
    return uid

def get_target_module_by_name(data, target_name):  
    for i in data:
        if i['name'] == target_name:
            t_module = i
    return t_module

def get_target_content_from_module_by_name(module, target_name):
    for i in module['data']:
        if i['name'] == target_name:
            t_content = i
    
    return t_content['data']

def get_datasets(data):
    basic_info = [i for i in data if i['name']=="基本信息"]
    datasets_part = [i for i in basic_info[0]['data'] if i['name']=="数据集"]
    ds_fname = datasets_part[0]['data'][0]['filename']
    ds_url = datasets_part[0]['data'][0]['url']
    upload_token = re.split('&',re.split('=', ds_url)[1])[0]
    ds_data = requests.get(ds_url)
    ds_fname0 = os.path.splitext(ds_fname)[0]
    with open(ds_fname0+'.zip', 'wb') as f:
        f.write(ds_data.content)
    return ds_fname0, upload_token

def get_ml_setup(data):
    ml_setup = get_target_module_by_name(data, "机器学习相关配置")
    label_type = get_target_content_from_module_by_name(ml_setup, "待测性质类型")[0]
    dscrpt_type = get_target_content_from_module_by_name(ml_setup, "描述符类型")[0]
    print(dscrpt_type)
    
    # if dscrpt_type not in dscrpt_options:
    #     res = "error"
    # else:
    res = dscrpt_type, label_type

    return res

def unzip_file(zip_path, unzip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_path)
    return None

def get_species(atoms_list):
    species = []
    for i in atoms_list:
        s = i.get_atomic_numbers()
        for j in s:
            if j not in species:
                species.append(j)
            else:
                continue
    return species

def get_ds_fname_list(data):
    return data[0]['data'][2]['data']

def generate_dscrpt(atoms, dscrpt_type, label_type):
    if dscrpt_type in ['None', 'SOAP']:
        soap_prms = {
            'species': get_species(atoms),
            'periodic': True,
            'r_cut': 8.0,
            'n_max': 5,
            'l_max': 5,
            'average': 'inner'
        }
        soap = SOAP(**soap_prms)

        if len(atoms) > 4000:
            np.random.shuffle(atoms)
            atoms = atoms[:4000]

        dscrpts = soap.create(atoms, n_jobs=5)

    
    if label_type == 'energy':
        label = np.array([a.get_total_energy()/a.get_global_number_of_atoms() for a in atoms])

    tds_dscrpt = np.concatenate((dscrpts, label.reshape(-1, 1)), axis=1)

    return tds_dscrpt

def upload_big_file(file, name_id, uid, headers):
    split_list = list(range(0, len(file), 1000000))

    for i in split_list:
        if i == split_list[-1]:
            last = 1
        else:
            last = 0
        
        upload_bigfile = requests.post(
            url = "https://eln.iphy.ac.cn:61263/open_eln/eln_api_bigupload.php",
            data = {
                'uid': uid,
                'name': name_id,
                'last': last
            },
            files = [
                ('file', (name_id, file[i:i + 1000000]))
            ],
            headers = headers
        )
    
    return upload_bigfile.json()['errcode']

@app.post("/")
async def nowtime(request_data: Request):
    # get datasets
    data = await request_data.json()
    try:
        ds_zip_fname, upload_token = get_datasets(data)
    except:
        data1 = {
            "errcode": 2,
            "errmsg": "数据集读取有误，请检查数据集"
        }

    unzip_file("./"+ds_zip_fname+".zip", ds_zip_fname)

    # read datasets
    ds_fnames = get_ds_fname_list(data)
    tds = ds_fnames[0]
    tds_path = os.path.join(".",ds_zip_fname,"ds_"+tds+".pkl")
    with open(tds_path, 'rb') as f:
        tds_data = pickle.load(f)

    # generate dscriptors
    try:
        dscrpt_type, label_type = get_ml_setup(data)
    except:
        data1 = {
            "errcode": 2,
            "errmsg": "未正确读取机器学习配置模块，请检查"
        }

    if dscrpt_options == 'error':
        data1 = {
            "errcode": 2,
            "errmsg": "不支持该描述符类型，请重新选择"
        }
    

    tds_dscrpt = generate_dscrpt(tds_data, dscrpt_type, label_type)
    np.savetxt("dscrpt.txt", tds_dscrpt)

    # upload descriptors
    with open("./dscrpt.txt", 'r') as f:
        tds_dscrpt = f.read()

    ds_id = 'dscrpt_'+gen_uid()+'.txt'

    upload_big_file(
        tds_dscrpt,
        ds_id,
        str(upload_token),
        {'Authorization': 'Bearer ' + upload_token}
    )


    data1 = {
        "errcode":0,
        "addModule":[
            {
                "name":"机器学习",
                "type":"form"
            }
        ],
        "add":[
            {
                "module":"机器学习",
                "type":"file",
                "name":"描述符",
                "data":["#file{%s}"%ds_id]
            }
        ],
        "message":[
            "已生成描述符，可以开始训练模型"
        ]
    }

    dir_name = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    os.mkdir(dir_name)
    shutil.move(ds_zip_fname, dir_name)
    shutil.move("./dscrpt.txt", dir_name)
    shutil.move("datasets.zip", dir_name)

    return data1

if __name__ == '__main__':
    import uvicorn

uvicorn.run(app=app, host="**.***.*.*", workers=1, port=****)
