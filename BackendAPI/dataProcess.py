# -*- coding: UTF-8 -*-
import numpy as np
import pandas as pd
import json
import time
import sys
import os
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS

import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath


__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '../..')))
os.environ["FLAGS_allocator_strategy"] = 'auto_growth'
from pathlib import Path
import base64
import shutil
import time
from werkzeug.utils import secure_filename

import cv2

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from tools.infer.predict_rec import ModifiyOCR,replacement
from detect import run, parse_opt
# rec
import tools.infer.utility as utility
from ppocr.utils.logging import get_logger
from ppocr.utils.utility import get_image_file_list, check_and_read_gif

#os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
logger = get_logger()

app = Flask(__name__)

CORS(app)
txt = str()
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def detect_read_files():
    filenames = [x.split(".jpg")[0] for x in os.listdir('InputImage')]
    classes = pd.read_csv('classesOri.txt', index_col=None, header=None)
    return filenames, classes

def detect_to_cv2_bbox(bbox, img_shape):
    bbox = [(bbox[1]-bbox[3]/2)*img_shape[0], (bbox[1]+bbox[3]/2)*img_shape[0], (bbox[0]-bbox[2]/2)*img_shape[1], (bbox[0]+bbox[2]/2)*img_shape[1]]
    bbox = [round(x) for x in bbox]
    return bbox

def detect_export_tagged_image():
    filenames, classes = detect_read_files()
    for filename in filenames:
        img = cv2.imdecode(np.fromfile(r'InputImage/%s.jpg' %filename, dtype=np.uint8), -1)                
        labels = pd.read_csv('runs/detect/exp/labels/' + filename + '.txt', index_col=0, header=None, sep=' ')
        img_shape = img.shape
        ids = np.zeros_like(classes)
        for row in labels.iterrows():
            ids[row[0]] += 1
            bbox = detect_to_cv2_bbox(row[1].to_list(), img_shape)
            img_class = img[bbox[0]:bbox[1], bbox[2]:bbox[3]]
            export_filename = './outputImage/tagged_image/' + classes[0][row[0]] + '/' + f"{filename}_{ids[row[0]]}.jpg"
            cv2.imencode('.jpg', img_class)[1].tofile(export_filename)



def uniqueFileName(target, output):
    df = pd.read_csv(target,sep='\t',index_col=0)
    df =df.astype(str)
    kk=df.groupby(['file']).apply(lambda group: '&'.join(group['prediction']))
    kk.to_csv(output, sep='\t', mode='a')
   



def remove_files_based_on_classes(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip() 
                txt_file = line + ".txt"
                txt_file_2 = line + "2.txt"
                json_file = line + ".json"
                
      
                for file in [txt_file, txt_file_2, json_file]:
                    try:
                        os.remove(file)
                        print(f"Deleted {file}")
                    except FileNotFoundError:
                        print(f"{file} not found, skipping.")
    except FileNotFoundError as e:
        print(f"Error: {e}")

def delete_and_create_directories(base_path, classes_file_path):

    shutil.rmtree('./outputImage/tagged_image')
    shutil.rmtree('./InputImage')
    shutil.rmtree('./runs')
    

    input_image_path = os.path.join(base_path, 'InputImage')
    tagged_image_path = os.path.join(base_path, 'outputImage', 'tagged_image')
    os.makedirs(input_image_path)
    os.makedirs(tagged_image_path)

 
    try:
        with open(classes_file_path, 'r') as file:
            for line in file:
                class_name = line.strip()
                class_dir_path = os.path.join(tagged_image_path, class_name)
                os.makedirs(class_dir_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")   
       

def process_text_to_json(targetfile, column, jsonfile):
   
    with open(targetfile, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:] 


    with open(jsonfile, 'w', encoding='utf-8') as outfile:
        for line in lines:
          
            parts = line.strip().split()
            if len(parts) >= 2: 
                data_json = {
                    "name": parts[0],
                    column: parts[1]
                }
                
                json.dump(data_json, outfile, ensure_ascii=False)
                outfile.write("\n")
            else:
                print(f"Skipping line due to insufficient data: {line.strip()}")

         
def process_files_based_on_classes(file_path):
    try:
        with open(file_path, 'r') as classes_file:
            for line in classes_file:
                attribute_name = line.strip()
                original_file = f'./{attribute_name}.txt'
                updated_file = f'./{attribute_name}2.txt'
                json_file = f'{attribute_name}.json'
                
                uniqueFileName(original_file, updated_file)
                

                input_file_for_json = updated_file
                
                process_text_to_json(input_file_for_json, attribute_name, json_file)
    except FileNotFoundError as e:
        print(f"Error: {e}") 

def merge_json_files_based_on_classes(file_path='classes.txt'):
    # 读取类别名称
    with open(file_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    
    df_merged = None

    for class_name in classes:
        json_file_path = f'{class_name}.json'
        
        df_temp = pd.read_json(json_file_path, lines=True)
        
        if df_merged is None:
            df_merged = df_temp
        else:
            df_merged = df_merged.merge(df_temp, on='name', how='outer')
    
    return df_merged               
            
def makeRecordFile():
    with open("classes.txt", "r") as file:
        class_names = file.readlines()
    
    for class_name in class_names:
        class_name = class_name.strip()  
        
        file_path = f"{class_name}.txt"
        with open(file_path, "w+") as text_file:
            pass 
def load_json_to_df(classes_file):
    dataframes = {}  
    with open(classes_file, "r") as file:
        class_names = file.read().splitlines()

    for class_name in class_names:
        json_file = f'{class_name}.json'  
        try:
            df = pd.read_json(json_file, lines=True)  
            dataframes[class_name] = df  
        except Exception as e:
            print(f"Error loading {json_file}: {e}") 

    return dataframes
def encode_images_in_directory(directory="./InputImage"):
    image_data = []
    directory = os.path.normpath(directory)
    
    for filename in os.listdir(directory):
        filename = filename.replace(".jpg" , "")
        photo_path = os.path.join('./outputImage/tagged_image/Photo', f'{filename}_[1].jpg')
        print(photo_path)
        sig_path = os.path.join('./outputImage/tagged_image/Sig', f'{filename}_[1].jpg')
        print(sig_path)
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as image_file:
                photo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            photo_base64 = "None"

        if os.path.exists(sig_path):
            with open(sig_path, "rb") as image_file:
                sig_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            sig_base64 = "None"

        image_data.append({
            "name": filename,
            "photo": photo_base64,
            "sig": sig_base64
        })

    return image_data
