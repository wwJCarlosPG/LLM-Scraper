from tester.dataset_labeler import FireworksLLMLabeler
import os
import json
from pydantic_ai.usage import Usage
from scraper_manager.application.extraction.extractor import DataExtractor

def generate_labeled_dataset():
    dest_path = 'pages/labeled_dataset/amazon_best_sellers_fashion'
    os.makedirs(dest_path, exist_ok=True)

    root_path = "pages/amazon_best_sellers"
    files = os.listdir(root_path)
    llm_labeler = FireworksLLMLabeler("fw_3ZfAFkx4wwfRovV1t2NrFJsh")
    total = len(files)
    print(f'Total: {total}')

    # def clean_years(years, files):
    #     root_path = "pages/dataset/nytimes"
    #     for file in files:
    #         for year in years:
    #             if str(year) in file:
    #                 if os.path.exists(os.path.join(root_path,file)):
    #                     os.remove(os.path.join(root_path,file))
        
    # clean_years([2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, '__2__', '__4__', '__6__', '__8__', '__10__', '__12__'], files)
    
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

async def test(site: str, extractor: DataExtractor, refinement: bool, cot: bool,self_consistency, dest_path: str, llm_result_path: str):
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
                            agent_response = await extractor.extract(query, html_content=html_content, selfconsistency=self_consistency, refinement=refinement, cot=cot)
                        except Exception as e:
                            print(f"Finalizado con error {htmls[i]}:query{j+1} ---> {e}")
                            with open(f'{llm_result_path}/with_selfconsistency_errors.txt','a') as processed:
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

async def test2(site: str, extractor: DataExtractor, model, refinement, cot):
    if refinement and cot:
        dir = 'with_refinement_and_cot'
    elif not refinement and cot:
        dir = 'without_refinement_with_cot'
    
    dest_path = f'code/results/{site}/{model}/{dir}'
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
                    agent_response = await extractor.extract(query, html_content=html_content, selfconsistency=False, refinement=refinement, cot=cot)
                except Exception as e:
                    print(f"Finalizado con error {html_files[i]}: {e}")
                try:
                    usage = agent_response[1]
                    agent_response = agent_response[0]
                except Exception as e:
                    print(f"Usage error {html_files[i]}: {e}")
                    usage = Usage(request_tokens=len(query)+len(html_content),response_tokens=len(agent_response.explanation),total_tokens=len(query)+len(html_content))
                responses[indexs[i]-1][f'response{indexs[i]}'] = {
                        "scraped_data": agent_response.scraped_data,
                        'explanation': agent_response.explanation,
                        'feedback': agent_response.feedback,
                        'refinement_count': agent_response.refinement_count,
                        'request_tokens': usage.request_tokens,
                        'response_tokens': usage.response_tokens,
                        'total_tokens': usage.total_tokens
                    }
                with open(os.path.join(dest_path, files[i]), 'w') as updated_file:
                    print(f"Updated {os.path.join(dest_path, files[i])}")
                    json.dump(labeled_data, updated_file, indent=4)
                            
                    with open('code/results/processed.txt','a') as processed:
                        processed.write(f'\n {queries[i]}: {html_files[i]}')
                        print(f'Processed {queries[i]}: {html_files[i]}')


def collect_errors(site):
    dest_path = f'code/results/{site}/llama3.3-70B/without_refinement_with_cot'

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
                except KeyError as e:
                    with open('code/results/errors.txt', 'a') as errors:
                            errors.write(f'\n{dir}: query{i+1}')
                except Exception as e:
                    print(e)
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



def make_equal_queries():
    d1 = 'code/results/bbc/llama3.3-70B/with_refinement_and_cot'
    d2 = 'code/results/bbc/llama3.3-70B/without_refinement_with_cot'
    dirs1 = os.listdir(d1)
    dirs2 = os.listdir(d2)

    for i in range(len(dirs1)):
        make_equal_queries_and_remove_response(os.path.join(d1,dirs1[i]), os.path.join(d2,dirs2[i])) 



def make_equal_queries_and_remove_response(path1: str, path2: str):
    with open(path1, 'r') as file:
        data = json.load(file)
        responses1 = data['responses']
        # print(responses1[0])
        print('\n')
        with open(path2, 'r') as file2:
            data2 = json.load(file2)
            responses2 = data2['responses']
            # print(responses2[0])

            for i in range(len(responses1)):
                try:
                    if responses1[i][f'query{i+1}'] != responses2[i][f'query{i+1}']:
                        responses2[i][f'query{i+1}'] = responses1[i][f'query{i+1}']
                        responses2[i][f'data{i+1}'] = responses1[i][f'data{i+1}']
                        with open(path2, 'w') as file2:
                            json.dump(data2, file2, indent=4)
                            print(f'Updated {path2}')
                        # print(file)
                except Exception as e:
                    print(file.name)
                    print(file2.name)
                    # print(responses2[i])
                    print(e)
                    return




        
        
