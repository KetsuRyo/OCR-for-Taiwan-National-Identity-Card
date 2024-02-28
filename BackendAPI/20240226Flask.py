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
import shutil
import time
from werkzeug.utils import secure_filename


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
from dataProcess import encode_images_in_directory, detect_export_tagged_image, remove_files_based_on_classes , delete_and_create_directories ,process_files_based_on_classes,merge_json_files_based_on_classes,makeRecordFile

#os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
logger = get_logger()

app = Flask(__name__)

CORS(app)
txt = str()
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



def OCR(image_dir, output):
    args=utility.parse_args()
    args.use_gpu=False
    args.use_mp=True
    args.enable_mkldnn =False
    args.image_dir= image_dir
    args.det_model_dir= "./InferenceModel/ch_PP-OCRv4_det_server_infer" 
    args.rec_model_dir= "./InferenceModel/ch_PP-OCRv4_rec_server_infer" 
    args.rec_char_dict_path= "./ppocr/utils/ppocr_keys_v1.txt"
    ModifiyOCR(args, output)    

def batch_OCR_for_classes():
    with open("classes.txt", "r") as file:
        class_names = file.read().splitlines()
    
    for class_name in class_names:
        image_dir = f"./outputImage/tagged_image/{class_name}/"
        output = f"./{class_name}.txt"
        OCR(image_dir, output)






def yoloPredict():        
    opt2 = parse_opt()
    opt2.weights = './InferenceModel/yoloHeavy/best.pt'
    opt2.imgsz = (860, 1280)
    opt2.save_txt = True
    opt2.source = './InputImage'
    opt2.conf_thres = 0.25
    run(**vars(opt2))
    detect_export_tagged_image()


@app.after_request
def apply_caching(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


    
@app.route('/IDCard_Detection')
def index():
    return 'hello!!'

@app.route('/IDCard_Detection/predict', methods=['POST'])

def postInput():       
    ##  makeRecordFile to save OCR result
    makeRecordFile()   
    ##  delete last file
    delete_and_create_directories('.', 'classesOri.txt')   
    ## save upload file
    uploaded_files = request.files.getlist("file")
    for f in uploaded_files:
        upload_path = os.path.join('./InputImage',f.filename) 
        f.save(upload_path)
        shutil.copy2(upload_path, './backup')
    ## Start yolo
    start_time = time.time()   
    
    ## yolo identificaton and images classification
    yoloPredict()
    
    ## Record  yolo_identified_time
    yolo_identified_time =(time.time() - start_time)
    
    ## Start OCR
    start2_time = time.time()
    batch_OCR_for_classes()    
    ## Record  yolo_identified_time
    OCR_time = (time.time() - start2_time)
    ## turn txt result to json
    process_files_based_on_classes("classes.txt")
    ## process exported json with pandas dataframe
    df_final = merge_json_files_based_on_classes()

    result = df_final.to_json(orient="split")
    parsed = json.loads(result)
    json.dumps(parsed, indent=4)  
    ## remove intermediate file
    remove_files_based_on_classes("classes.txt")
    ## process image
    image_data = encode_images_in_directory()

    # Construct the final response
    final_response = {
        "OCR": parsed,  # Assuming 'parsed' is your final OCR JSON result
        "image": image_data,
        "classify Time":yolo_identified_time,
        "OCR Time":OCR_time
    }

    # Return the final JSON response
    return jsonify(final_response)

                   
                  

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8689, debug=True,threaded=True)