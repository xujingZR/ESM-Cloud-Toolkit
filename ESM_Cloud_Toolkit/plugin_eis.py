# plugin
import os
import re
import requests
from fastapi import FastAPI, Request
from eis import eis
import warnings
import random
import string
import datetime

warnings.filterwarnings("ignore")

app = FastAPI()

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


def download_files(content, t_dir):
    fnames = []
    for i in content:
        fname = i['filename']
        url = i['url']
        # replace https://eln.iphy.ac.cn:61263 with http://172.16.8.28
        url = url.replace("https://eln.iphy.ac.cn:61263", "http://172.16.8.28")
        data = requests.get(url)
        os.chdir(t_dir)
        with open(fname, 'wb') as f:
            f.write(data.content)
        fnames.append(fname)
    upload_token = re.split('&',re.split('=', url)[1])[0]

    return fnames, upload_token

def upload_big_file(file_path, name_id, upload_token):

    with open(file_path, 'rb') as f:
        file = f.read()
    
    uid = gen_uid()
    
    split_list = list(range(0, len(file), 1000000))

    for i in split_list:
        if i == split_list[-1]:
            last = 1
        else:
            last = 0
    
    upload_bigfile = requests.post(
        url = "http://172.16.8.28/open_eln/eln_api_bigupload.php",
        data = {
            'uid': uid,
            'name': uid + name_id,
            'last': last
        },
        files = [
            ('file', (name_id, file[i:i + 1000000]))
        ],
        headers = {'Authorization': 'Bearer ' + upload_token}
    )

return uid+name_id, uid

@app.post("/")
async def nowtime(request_data: Request):
    data = await request_data.json()
    
    module_name = "交流阻抗谱基本设置"
    content_name_file = "文件"
    # content_name_cycle = "目标循环数"

    r_dir = r"/home/battery/xu/plugin/eis/eis"
    dir_name = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    t_dir = os.path.join(r_dir, dir_name)
    os.makedirs(t_dir)

    t_module = get_target_module_by_name(data, module_name)
    file_content = get_target_content_from_module_by_name(t_module, content_name_file)
    fnames, upload_token = download_files(file_content, t_dir = t_dir)
    t_file_path = [os.path.join(t_dir, fname) for fname in fnames]
    eis(t_file_path, fnames)

    name_id_1, uid_1 = upload_big_file(
        os.path.join(t_dir, "eis.png"),
        "eis.png",
        upload_token
    )

    return {
        "errcode":0,
        "add":[
            {
                "module": module_name,
                "type":"file",
                "name":"曲线",
                "data":["#file{%s}"%name_id_1]
            }
        ],
        "message":["Done!"]
    }

if __name__ == '__main__':
    import uvicorn

uvicorn.run(app=app, host="0.0.0.0", workers=1, port=****)
