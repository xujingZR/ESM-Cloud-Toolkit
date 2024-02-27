import os
import re
import requests
from fastapi import FastAPI, Request
import warnings
import random
import string
import datetime

from pptx import Presentation
from gen_ppt import add_1_pic
from gen_ppt import add_2_pics

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
    
    module_name_1 = "充放电数据基本设置"
    module_name_2 = "交流阻抗谱基本设置"
    content_name_file = "曲线"

    r_dir = r"/home/battery/xu/plugin/ppt/ppt"
    dir_name = datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    t_dir = os.path.join(r_dir, dir_name)
    os.makedirs(t_dir)

    t_module_1 = get_target_module_by_name(data, module_name_1)
    t_module_2 = get_target_module_by_name(data, module_name_2)
    
    file_content_1 = get_target_content_from_module_by_name(t_module_1, content_name_file)
    file_content_2 = get_target_content_from_module_by_name(t_module_2, content_name_file)

    fnames_1, upload_token = download_files(file_content_1, t_dir = t_dir)
    fnames_2, _ = download_files(file_content_2, t_dir = t_dir)
    t_file_path_1 = [os.path.join(t_dir, fname) for fname in fnames_1]
    t_file_path_2 = [os.path.join(t_dir, fname) for fname in fnames_2]

    # main func
    prs = Presentation()
    prs = add_2_pics(t_file_path_1[0], t_file_path_1[1], "循环性能", "首周对比", "长循
环对比", prs)
    prs = add_1_pic(t_file_path_2[0], "交流阻抗", "", prs)
    prs.save("结果.pptx")

    name_id_1, uid_1 = upload_big_file(
        os.path.join(t_dir, "结果.pptx"),
        "结果.pptx",
        upload_token
    )

    return {
        "errcode":0,
        "addModule":[
            {
                "name": "结果展示",
                "type": "form"
            }
        ],
        "add":[
            {
                "module": "结果展示",
                "type":"file",
                "name":"PPT",
                "data":["#file{%s}"%name_id_1]
            }
        ],
        "message":["Done!"]
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", workers=1, port=****)
