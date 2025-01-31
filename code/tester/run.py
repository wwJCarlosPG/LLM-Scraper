from tester.dataset_labeler import FireworksLLMLabeler
import os
import json
from pydantic_ai.usage import Usage
from scraper_manager.application.extraction.extractor import DataExtractor

def generate_labeled_dataset():
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

    print('Done')

async def test(site: str, extractor: DataExtractor, refinement: bool, cot: bool, dest_path: str, llm_result_path: str):
    labeled_ds = os.listdir(dest_path)
    htmls = os.listdir(f'pages/dataset/{site}')
    htmls.sort(key = lambda x: x.split('.')[0])
    labeled_ds.sort(key = lambda x: x.split('.')[0])
    print(len(htmls))
    print(len(labeled_ds))
    for i in range(len(htmls)):
        with open(os.path.join(dest_path, labeled_ds[i]), 'r') as labeled_file:
            labeled_data: dict = json.load(labeled_file)
            print(os.path.join(f'pages/dataset/{site}', htmls[i]))
            with open(f'{llm_result_path}/processed.txt','r') as processed:
                lines = [line.strip() for line in processed.readlines()]

                
                with open(os.path.join(f'pages/dataset/{site}', htmls[i]), 'r') as html:
                    html_content = html.read()

                    responses = labeled_data['responses']
                    for j in range(len(responses)):
                        query = responses[j][f'query{j+1}']
                        if f'{htmls[i]}:query{j+1}' in lines:
                            continue
                        try:
                            agent_response = await extractor.extract(query, html_content=html_content, selfconsistency=False, refinement=False)
                        except Exception as e:
                            print(f"Finalizado con error {htmls[i]}:query{j+1} ---> {e}")
                            with open(f'{llm_result_path}/with_refinement_and_cot_errors.txt','a') as processed:
                                processed.write(f'\n{htmls[i]}:query{j+1}')    
                        try:
                            usage = agent_response[1]
                            agent_response = agent_response[0]
                        except:
                            try:
                                if agent_response.scraped_data:
                                    usage = Usage(request_tokens=-1,response_tokens=len(agent_response.explanation),total_tokens=len(query)+len(html_content))
                            except Exception:
                                continue
                        responses[j][f'response{j+1}'] = {
                            "scraped_data": agent_response.scraped_data,
                            'explanation': agent_response.explanation,
                            'feedback': agent_response.feedback,
                            'refinement_count': agent_response.refinement_count,
                            'is_valid': agent_response.is_valid,
                            'request_tokens': usage.request_tokens,
                            'response_tokens': usage.response_tokens,
                            'total_tokens': usage.total_tokens
                        }
                    
                        with open(os.path.join(dest_path, labeled_ds[i]), 'w') as updated_file:
                            json.dump(labeled_data, updated_file, indent=4)
                            
                        with open(f'{llm_result_path}/processed.txt','a') as processed:
                            processed.write(f'\n{htmls[i]}:query{j+1}')    
                            print(f'\n{htmls[i]}:query{j+1}')

async def test2(site: str, extractor: DataExtractor):
    dest_path = f'code/results/{site}/without_refinement_with_cot'
    # labeled_ds = os.listdir(dest_path)
    # htmls = os.listdir(f'pages/dataset/{site}')
    # htmls.sort(key = lambda x: x.split('.')[0])
    # labeled_ds.sort(key = lambda x: x.split('.')[0])
    with open('code/results/errors.txt', 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    queries = [q.split(':')[1].strip() for q in lines]
    # print(queries)
    indexs = [int(q[5]) for q in queries]
    print(indexs)
    files = [f.split(':')[0].strip() for f in lines]
    html_files = [f.split('.')[0].split('.')[0]+'.html'.strip() for f in files]

    for i in range(len(files)):
        with open(os.path.join(f'pages/dataset/{site}', html_files[i])) as html:
            html_content = html.read()
            with open(os.path.join(dest_path, files[i]), 'r') as labeled_file:
                labeled_data = json.load(labeled_file)
                responses = labeled_data['responses']
                
                query = responses[indexs[i]-1][queries[i]]
                try:
                    agent_response = await extractor.extract(query, html_content=html_content, selfconsistency=False, refinement=False)
                except Exception as e:
                    print(f"Finalizado con error {html_files[i]}: {e}")
                try:
                    usage = agent_response[1]
                    agent_response = agent_response[0]
                except Exception as e:
                    print(f"Usage error {html_files[i]}: {e}")
                    usage = Usage(request_tokens=len(query)+len(html),response_tokens=len(agent_response.explanation),total_tokens=len(query)+len(html))
                responses[indexs[i]-1][f'response{indexs[i]-1}'] = {
                        "scraped_data": agent_response.scraped_data,
                        'explanation': agent_response.explanation,
                        'feedback': agent_response.feedback,
                        'refinement_count': agent_response.refinement_count,
                        'request_tokens': usage.request_tokens,
                        'response_tokens': usage.response_tokens,
                        'total_tokens': usage.total_tokens
                    }
                with open(os.path.join(dest_path, files[i]), 'w') as updated_file:
                    json.dump(labeled_data, updated_file, indent=4)
                            
                    with open('code/results/processed.txt','a') as processed:
                        processed.write(f'\n {queries[i]}: {html_files[i]}')



def collect_errors(site):
    dest_path = f'code/results/{site}/without_refinement_with_cot'

    dirs = os.listdir(dest_path)
    for dir in dirs:
        with open(os.path.join(dest_path, dir), 'r') as file:
            data = json.load(file)
            responses = data['responses']
            for i in range(len(responses)):
                
                try:
                    if responses[i][f'response{i+1}']['scraped_data'] == []:
                        with open('code/results/errors.txt', 'a') as errors:
                            errors.write(f'\n{dir}: query{i+1}')
                except Exception:
                    print(dir)
                    return
                

def sort_txt():
    with open('code/results/errors.txt', 'r') as file:
        lines = file.readlines()
        lines.sort(key= lambda x: x.split(':')[0])
        with open('code/results/errors.txt', 'w') as file:
            # for line in lines:
            #     file.write("\n")
            for line in lines:
                file.write(line)

def remove_duplicates():
    with open('code/results/errors.txt', 'r') as file:
        lines = file.readlines()
        lines = list(set(lines))
        with open('code/results/errors.txt', 'w') as file:
            for line in lines:
                file.write(line)

                    





        
        
