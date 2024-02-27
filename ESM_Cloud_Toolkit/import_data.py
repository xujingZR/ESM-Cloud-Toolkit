"""automatic DFT data uploading script"""
import os
import json
import requests
import zipfile
import shutil
import pickle
import random
import string
from tqdm import tqdm
from fnmatch import fnmatch

from pymatgen.io.vasp.outputs import Vasprun
from ase.io import read

import warnings
warnings.filterwarnings('ignore')

def login_eln(username, password):
    # Login and get access token
    # request url
    token_url = "https://in.iphy.ac.cn/open/tokens2.php"

    id_passwd = {
        'username': username,
        'password': password
    }

    res = requests.post(token_url, data=id_passwd)
    res = res.json()

    if res['errcode'] == 0:
        access_token = res['access']['token']
        print('Login success!')

    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    return headers

def find_types(tlist):
    # get calculation types
    n_types = 0
    types_count = {}
    exceptions = []

    for dir in tlist:
        t_path = os.path.join(tpath, dir)
        if os.path.isdir(t_path):
            os.chdir(t_path)
        else:
            continue
        files = os.listdir(".")
        dirs = [x for x in files if os.path.isdir(x)]

        dirs = tuple(dirs)
        if dirs in types_count:
            types_count[dirs] += 1
        else:
            types_count[dirs] = 1
            n_types += 1
            if n_types > 1:
                exceptions.append(os.getcwd())

    return types_count, exceptions

def get_element(tlist):
    # get elemental type
    element = {}
    for dir in tlist:
        t_path = os.path.join(tpath, dir)
        if os.path.isdir(t_path):
            os.chdir(t_path)
        else:
            continue
        dirs = os.listdir(".")
        dirs = [x for x in dirs if os.path.isdir(x)]

        cpath = os.getcwd()
        for d in dirs:
            with open(os.path.join(cpath, d, "POSCAR"), 'r') as f:
                poscar = f.readlines()
                es = poscar[5].split()
                for e in es:
                    if e in element:
                        element[e] += 1
                    else:
                        element[e] = 1

    e = '/'.join(list(element.keys()))
    return e

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, relative_path)

def get_incars(tlist):
    incars = {}
    for dir in tlist:
        t_path = os.path.join(tpath, dir)
        if os.path.isdir(t_path):
            os.chdir(t_path)
        else:
            continue
        dirs = os.listdir(".")
        dirs = [x for x in dirs if os.path.isdir(x)]

        cpath = os.getcwd()
        for d in dirs:
            try:
                with open(os.path.join(cpath, d, "INCAR"), 'r') as f:
                    incar = f.readlines()
                    incar = tuple(incar)
                    if incar in incars:
                        incars[incar] += 1
                    else:
                        incars[incar] = 1
            except:
                print("No INCAR in {}".format(os.path.join(cpath, d)))
    return list(incars.keys())

def upload_file(eln_name, name_id, filename, headers):

    up_file_url = "https://eln.iphy.ac.cn:61263/open_eln/eln_api_upload.php"

    with open(filename, 'rb') as f:
        f_data = f.read()

    upload_file = requests.post(
        url = up_file_url,
        data = {
            'eln': eln_name,
            'file': f_data,
            'name': name_id
        },
        files = [('file', (name_id, f_data))],
        headers = headers
    )

    if upload_file.json()['errcode'] == 0:
        print("Upload file successfully!")
        r = None
    else:
        print("Upload file failed!")
        r = upload_file.json()

    return r

def upload_data(eln_name, record_name, uid, cal_target, e, r, ht, tpath,dataset_size, headers):
    upload_url = "https://eln.iphy.ac.cn:61263/open_eln/eln_api_import.php"

    upload_data = {
        "eln": eln_name,
        "template": "基础计算模板",
        "dataset": [{
            "title": record_name,
            "uid": uid,
            "data": {
                "基本信息": {
                    "计算目的": cal_target,
                    "相关元素/化学式": e,
                    "计算类型": r,
                    "计算参数": ["#file{%s}"%'incar.zip'],
                    "是否高通量": ht,
                    "数据集": ["#file{%s}"%'datasets.zip'],
                    "数据集尺寸": dataset_size,
                    "文件路径": tpath,
                }
            }
            }]
    }

    res = requests.post(upload_url, data=json.dumps(upload_data), headers = headers)

    if res.json()['errcode'] == 0:
        print(res.json()['errmsg'])
        r = None
    else:
        print(res.json()['errmsg'])
        r = res.json()

    return r

def check_convergence(vasprun):
    """
    check whether the electronic steps are converged
    """
    unconverge_index = []
    for i in range(len(vasprun.ionic_steps)):
        if len(vasprun.ionic_steps[i]['electronic_steps'])<vasprun.parameters['NELM']:
            continue
        else:
            unconverge_index.append(i)
            # print("the %dth ionic step is not converged"%(i))
    
    all_atoms = read("vasprun.xml",format='vasp-xml',index=slice(0,None))
    if len(unconverge_index) == 0:
        add_atoms = all_atoms
    else:
        start_index = max(unconverge_index) + 1
        add_atoms = all_atoms[start_index:]
    if len(add_atoms) < 100:
        return []
    else:
        return add_atoms

def get_dataset_from_single_cal(single_cal_path):
    try:
        os.chdir(single_cal_path)
        vasprun = Vasprun('vasprun.xml')
        r = check_convergence(vasprun)  
    except:
        print(f"!!! {single_cal_path} can not be parsed correctly!!!")
        r = []

    return r
    

def get_dataset_from_caltype(tlist, caltype):

    atoms = []
    tdir = [os.path.join(tpath, i, caltype) for i in tlist]
    for i in tdir:
        if os.path.isdir(i):
            atoms.extend(get_dataset_from_single_cal(i))    
        else:
            continue
    
    return atoms

def flatten_list(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            lst.extend(item)
        else:
            lst.append(item)
    return result
    
def dump_datasets(caltype):
    if fnmatch(caltype, '*rlx*'):
        atoms = get_dataset_from_caltype(tlist, caltype)
        with open(os.path.join(datasets_path, 'ds_{}.pkl'.format(caltype)), 'wb') as f:
            pickle.dump(atoms, f)

def upload_big_file(file_path, name_id, uid):
    with open(file_path, 'rb') as f:
        file_data = f.read()

    split_list = list(range(0, len(file_data), 1000000))

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
                ('file', (name_id, file_data[i:i + 1000000]))
            ],
            headers = headers
        )
    
    return upload_bigfile.json()['errcode']

def gen_uid():
    uid = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    uid.upper()
    return uid

def get_dataset_size(t_path):
    os.chdir(t_path)
    datasets_size = []
    files = os.listdir(".")
    for i in files:
        with open(os.path.join(t_path, i), 'rb') as f:
            data = pickle.load(f)
        datasets_size.append(len(data))
    return datasets_size

c_path = os.getcwd()
with open(os.path.join(c_path, "prms.json"), 'rb') as f:
    prms = json.load(f)

tpath = prms["数据路径"]
n_processors = prms["进程数"]
eln_name = prms["记录本名称"]
uid = prms['uid']
record_name = prms['记录名称']

if len(str(uid)) != 16:
    uid = gen_uid()
else:
    uid = uid.upper()

# login eln
headers = login_eln(prms['用户名'], prms['密码'])

# 计算目的
cal_target = prms['计算目的']

# 计算类型
tlist = os.listdir(tpath)
types, exceptions = find_types(tlist)
r = list(list(types.keys())[0])

# 获取元素
e = get_element(tlist)

# 计算参数
incars = get_incars(tlist)

## 写入incars
os.mkdir(os.path.join(tpath, 'incars'))
for i in range(len(incars)):
    with open(os.path.join(tpath, 'incars', f"INCAR_{i}"), 'w') as f:
        f.write(''.join((incars[i])))
unzip_folder = os.path.join(tpath, 'incars')
zipped_folder = os.path.join(tpath, 'incars.zip')
## 压缩incars
zip_folder(unzip_folder, zipped_folder)
shutil.rmtree(unzip_folder)

res = upload_file(eln_name, 'incar.zip', zipped_folder, headers)
os.remove(zipped_folder)

# 是否高通量计算 
if len(tlist) > 10:
    ht = True
else:
    ht = False

# 生成datasets
print(format("生成数据集","=^20"))
datasets_path = os.path.join(tpath, 'datasets')
if os.path.exists(datasets_path):
    pass
else:
    os.mkdir(datasets_path)
for i in tqdm(r):
    dump_datasets(i)
zip_folder(datasets_path, os.path.join(tpath, 'datasets.zip'))

# 数据集尺寸
dataset_size = get_dataset_size(os.path.join(tpath, 'datasets'))
dataset_size = '/'.join([str(i) for i in dataset_size])

print(format("="*20))
for _ in range(10):
    upload_big_file(os.path.join(tpath, 'datasets.zip'), 'datasets.zip', uid)
    res = upload_data(eln_name, record_name, uid, cal_target, e, r, ht, tpath, dataset_size, headers)
    if res is None:
        break

    res_errmessage = res['errmsg']
    if fnmatch(res_errmessage, '*已经存在*'):
        uid = gen_uid()
        print(f"uid already exists, generate a new one {uid}!")
    else:
        print("Upload data successfully!")
        break

os.remove(os.path.join(tpath, 'datasets.zip'))
