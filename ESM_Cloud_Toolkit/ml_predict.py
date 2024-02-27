import re
import os
import zipfile
import requests
from fastapi import FastAPI, Request
from dscribe.descriptors import SOAP
import numpy as np
import ase.io
import joblib

import datetime
import shutil

app = FastAPI()

def get_file_from_module(name, module_data):

    for i in module_data:
        if i['name']==name:
            url = i['data'][0]['url']
            fname = i['data'][0]['filename']
            upload_token = re.split('&',re.split('=', url)[1])[0]
            data = requests.get(url)
            with open(fname, 'wb') as f:
                f.write(data.content)
    
    print(f"{fname} is written to {os.path.join(os.getcwd(), fname)}")
    return fname, upload_token

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

def generate_dscrpt(atoms, *, with_e=True):

    if isinstance(atoms, ase.Atoms):
        atoms = [atoms]

    soap_prms = {
        'species': get_species(atoms),
        'periodic': True,
        'r_cut': 8.0,
        'n_max': 5,
        'l_max': 5,
        'average': 'inner'
    }
    soap = SOAP(**soap_prms)

    dscrpts = soap.create(atoms)
    if with_e:
        e = np.array([a.get_total_energy()/a.get_global_number_of_atoms() for a in atoms])
        tds_dscrpt = np.concatenate((dscrpts, e.reshape(-1, 1)), axis=1)
    else:
        tds_dscrpt = dscrpts.reshape(-1, soap.get_number_of_features())

    return tds_dscrpt

@app.post("/")
async def nowtime(request_data: Request):
    # get unpredicted struc and model
    data = await request_data.json()
    ml_data = [i for i in data if i['name'] == '机器学习']
    model_fname, upload_token = get_file_from_module("model", ml_data[0]['data'])
    unpredicted_struc_fname, _ = get_file_from_module("待预测结构", ml_data[0]['data'])

    # upzip file
    unzip_file(model_fname, "./model")
    unzip_file(unpredicted_struc_fname, "./unpredict/")

    # generate descriptors for unpredicted_struc
    cpath = os.getcwd()
    unpred_path = os.path.join(cpath, "unpredict")
    struc_list = os.listdir(unpred_path)
    atoms = [ase.io.read(os.path.join(unpred_path, j)) for j in struc_list]

    dscrpt = generate_dscrpt(atoms, with_e=False)

    # load model and predict
    model = joblib.load("./model/model.pkl")
    res = model.predict(dscrpt)

    format_func = lambda i:format(i, "0.3f") + " eV/atom"

    res = [format_func(i) for i in res]

    data1 = {
        "errcode":0,
        "add":[
            {
                "module":"机器学习",
                "type":"text",
                "name":"预测值",
                "data":res[0]
            }
        ],
        "message":[
            "预测已完成"
        ]
    }

    dir_name = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    os.mkdir(dir_name)
    shutil.move(model_fname, dir_name)
    shutil.move("model", dir_name)
    os.remove(unpredicted_struc_fname)
    
    

    return data1

if __name__ == '__main__':
    import uvicorn

uvicorn.run(app=app, host="**.***.*.*", workers=1, port=****)
