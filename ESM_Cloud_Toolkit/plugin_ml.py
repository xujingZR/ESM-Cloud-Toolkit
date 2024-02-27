import numpy as np

import os
import re
import requests
from fastapi import FastAPI, Request
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import max_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
import joblib
import zipfile
import time

import random
import string

import matplotlib.pyplot as plt
import datetime
import shutil

app = FastAPI()

def gen_uid():
    uid = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    uid.upper()
    return uid


def get_dscrpt(data):
    ml_data = [i for i in data if i['name'] == '机器学习']
    dscrpt_fname = ml_data[0]['data'][0]['data'][0]['filename']
    dscrpt_url = ml_data[0]['data'][0]['data'][0]['url']
    upload_token = re.split('&',re.split('=', dscrpt_url)[1])[0]
    dscrpt_data = requests.get(dscrpt_url)
    with open(dscrpt_fname, 'wb') as f:
        f.write(dscrpt_data.content)
    return dscrpt_fname, upload_token

def fit_model(dscrpts):
    dscrpt = dscrpts[:, :-1]
    label = dscrpts[:, -1]

    X_train, X_test, y_train, y_test = train_test_split(
        dscrpt, label, test_size=0.2, random_state=42, shuffle=True
    )

    # pca
    # pca = PCA(n_components = 0.99999)
    # scaler = StandardScaler()
    # model
    regr = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=0)
    pipeline = Pipeline([
        # ('pca', pca),
        # ('scaler', scaler),
        ('model', regr)
    ])
    pipeline.fit(X_train, y_train)
    # save model
    joblib.dump(pipeline, "./model.pkl")

    return X_train, X_test, y_train, y_test, pipeline


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
    
    return upload_bigfile.json()

def zip_file(file2compress, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file2compress)
    return None

def get_metrics(y, y_pred):
    mae = mean_absolute_error(y, y_pred)
    max_e = max_error(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    return mae, max_e, mse, r2

def evaluate_model(X_train, X_test, y_train, y_test, pipeline):
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

    train_res = get_metrics(y_train, y_train_pred)
    test_res = get_metrics(y_test, y_test_pred)

    return y_train, y_test, y_train_pred, y_test_pred, train_res, test_res

def plot_performance(y_train, y_test, y_train_pred, y_test_pred, train_res, test_res):
    format_func = lambda i : format(i, "0.5f")
    train_res = list(train_res)
    test_res = list(test_res)
    train_res = [format_func(i) for i in train_res]
    test_res = [format_func(i) for i in test_res]

    fig = plt.figure(figsize=(6.4, 4.8))
    ax1 = fig.add_subplot(111)
    ax1.scatter(y_train_pred, y_train, marker='x')
    ax1.scatter(y_test_pred, y_test, marker='*')

    # baseline
    dot1 = [min(y_train), max(y_train)]
    dot2 = [min(y_train), max(y_train)]
    plt.plot(dot1, dot2, c='grey', ls='--')

    # 
    plt.xlabel("PRED (eV/atom)")
    plt.ylabel("REAL (eV/atom)")
    plt.title("MODEL PERFORMANCE")
    plt.legend(["train", "test"])
    fig.text(0.6, 0.5, "train_MAE: " + train_res[0] )
    fig.text(0.6, 0.45, "train_MAXE: " + train_res[1] )
    fig.text(0.6, 0.4, "train_MSE: " + train_res[2] )
    fig.text(0.6, 0.35, "train_R2: " + train_res[3])
    fig.text(0.6, 0.3, "test_MAE: " + test_res[0] )
    fig.text(0.6, 0.25, "test_MAXE: " + test_res[1] )
    fig.text(0.6, 0.2, "test_MSE: " + test_res[2] )
    fig.text(0.6, 0.15, "test_R2: " + test_res[3])

    fig.savefig("model_performance.png", dpi=500)

    return None



@app.post("/")
async def nowtime(request_data: Request):
    # get ml_data
    data = await request_data.json()
    dscrpt_fname, upload_token = get_dscrpt(data)

    start = time.time()
    with open(dscrpt_fname, 'rb') as f:
        dscrpt = np.loadtxt(f)

    # fit model
    res = fit_model(dscrpt)
    zip_file("./model.pkl", "./model.zip")
    
    with open("./model.zip", 'rb') as f:
        model = f.read()


    model_id = 'model_'+gen_uid()+'.zip'
    res_test = upload_big_file(
        model,
        model_id,
        str(upload_token),
        {'Authorization': 'Bearer ' + upload_token}
    )

    print("start evaluate model")
    # evaluate model
    y_res = evaluate_model(*res)
    
    # plot 
    plot_performance(*y_res)
    
    # upload png
    with open("./model_performance.png", 'rb') as f:
        model_perf_pic = f.read()
    
    perf_id = 'perf_'+gen_uid()+'.png'

    res = upload_big_file(
        model_perf_pic,
        perf_id,
        str(upload_token),
        {'Authorization': 'Bearer ' + upload_token}
    )


    data1 = {
        "errcode":0,
        "add":[
            {
                "module":"机器学习",
                "type":"file",
                "name":"model",
                "data":["#file{%s}"%model_id]
            },
            {
                "module":"机器学习",
                "type":"file",
                "name":"性能图片",
                "data":["#file{%s}"%perf_id]
            },
            {
                "module":"机器学习",
                "type":"file",
                "name":"待预测结构",
                "data":[]
            }
        ],
        "message":[
            "模型训练完成"
        ]
    }


    dir_name = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    os.mkdir(dir_name)
    shutil.move(dscrpt_fname, dir_name)
    shutil.move("./model.pkl", dir_name)
    shutil.move("model_performance.png", dir_name)
    os.remove("model.zip")

    print(data1)

    return data1

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app=app, host="**.***.*.*", workers=1, port=****)
