# OCR-for-Taiwan-National-Identity-Card

這是一個針對台灣國民身份證的光學字符識別(OCR)系統的開源專案，包含了前端和後端的實現。

## 前端設計理念

前端設計的理念和細節請參閱專案中的 [Frontend README](/SimpleFrontend/README.md)。

## 後端設計理念

後端設計的理念和細節請參閱專案中的 [Backend README](/BackendAPI/README.md)。

## 使用方法

### 1. 下載專案

使用git命令克隆專案到本地：

```bash
git clone https://github.com/KetsuRyo/OCR-for-Taiwan-National-Identity-Card.git
```

### 2. 安裝依賴

解壓縮專案後，在專案根目錄下使用pip命令安裝所需的依賴：

```bash
pip install -r requirements.txt
```

### 3. 下載模型

前往以下網址下載OCR所需的模型：

[模型下載地址](https://drive.google.com/file/d/15zqtvuAhm2ctfsGI-ulvfr5h6CFnt8J1/view?usp=drive_link)

下載後，將以下資料夾：

- ch_PP-OCRv4_det_infer
- ch_PP-OCRv4_det_server_infer
- ch_PP-OCRv4_rec_infer
- ch_PP-OCRv4_rec_server_infer
- yoloHeavy
- yoloLight

放在`BackendAPI/InferenceModel`資料夾中。

### 4. 運行後端API

進入`BackendAPI`目錄並執行Flask服務：

```bash
python 20240226Flask.py
```

在運行之前，請根據您的需要修改`20240226Flask.py`文件中的`app.run`行以設定主機和端口。

### 5. 設定前端

進入`SimpleFrontend`目錄
打開`public/script.js`文件，將其中的`http://host:port/IDCard_Detection/predict` (line 7)替換為您的Flask服務的主機地址和端口。
執行
```bash
npm install
```

### 6. 啟動前端

最後，執行
```bash
node server.js
```
以啟動前端應用。

### 7. DEMO 影片

[![DEMO 影片](http://img.youtube.com/vi/6K2WN1vRqLs/0.jpg)](http://www.youtube.com/watch?v=6K2WN1vRqLs "DEMO 影片")

