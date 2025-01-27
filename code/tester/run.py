from dataset_labeler import FireworksLLMLabeler
import os
import json


dest_path = 'pages/labeled_dataset/nytimes'
os.makedirs(dest_path, exist_ok=True)

root_path = "pages/dataset/nytimes"
files = os.listdir(root_path)
llm_labeler = FireworksLLMLabeler("fw_3ZKL6bqRbTf3SGtNKBLc9LGM")
total = len(files)
print(f'Total: {total}')

def clean_years(years, files):
    root_path = "pages/dataset/nytimes"
    for file in files:
        for year in years:
            if str(year) in file:
                if os.path.exists(os.path.join(root_path,file)):
                    os.remove(os.path.join(root_path,file))
    
clean_years([2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, '__2__', '__4__', '__6__', '__8__', '__10__', '__12__'], files)

for file in files:
    total = total-1
    print(f'Current: {total}')
    abs_path = os.path.join(root_path, file)
    try:
        with open(abs_path, 'r') as html:
            content = html.read()


            response = llm_labeler.labeling_dataset(content)
            json_data = json.loads(response)
            file_name = file.split('.')[0] + ".json"
            abs_dest_path = os.path.join(dest_path, file_name)
            with open(abs_dest_path, 'w') as labeled_file:
                json.dump(json_data, labeled_file, indent=4)

    except Exception as e:
        print(f'{e}: {file}')
        continue



        
        
