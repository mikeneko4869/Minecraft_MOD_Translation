from flask import Flask, request, render_template, send_file, jsonify
import os
import glob
import json
import zipfile
import time
from googletrans import Translator

app = Flask(__name__)

# グローバル変数
translated_data = {}
progress = 0

# 複数の en_us.json ファイルを読み込む
def read_json_files_from_jars(directory):
    lang_data = {}
    jar_files = glob.glob(os.path.join(directory, "*.jar"))

    for jar_file in jar_files:
        try:
            with zipfile.ZipFile(jar_file, 'r') as jar:
                file_path = "assets/すべてのファイル/lang/en_us.json"
                if file_path in jar.namelist():
                    with jar.open(file_path) as f:
                        data = json.load(f)
                        lang_data[jar_file] = data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file: {jar_file}")
            print(e)
        except Exception as e:
            print(f"Error processing jar file: {jar_file}")
            print(e)

    return lang_data

# 翻訳する関数
def translate_lang_data(lang_data, target_language):
    global progress
    translator = Translator()
    translated_data = {}
    
    for jar_file, entries in lang_data.items():
        translated_data[f"==========[{jar_file}]=========="] = {}
        total_keys = len(entries)
        
        for i, (key, value) in enumerate(entries.items()):
            try:
                translated = translator.translate(value, dest=target_language).text
                translated_data[f"==========[{jar_file}]=========="][key] = translated
            except Exception as e:
                print(f"Error translating key '{key}': {e}")
                translated_data[f"==========[{jar_file}]=========="][key] = value
            
            # 翻訳率の更新
            if total_keys > 0:
                progress = (i + 1) / total_keys * 100
        
    return translated_data

# 新しい .json ファイルに書き出す
def write_json_file(lang_data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(lang_data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global translated_data, progress
    progress = 0  # 進捗リセット
    
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    input_directory = 'mods'
    output_file = 'result/ja_jp.json'
    
    file.save(os.path.join(input_directory, file.filename))
    
    lang_data = read_json_files_from_jars(input_directory)
    translated_data = translate_lang_data(lang_data, target_language="ja")
    write_json_file(translated_data, output_file)
    
    return jsonify({"message": "Translation completed!", "progress": progress})

@app.route('/progress')
def get_progress():
    return jsonify({"progress": progress})

@app.route('/download')
def download_file():
    return send_file('result/ja_jp.json', as_attachment=True)

app.run()