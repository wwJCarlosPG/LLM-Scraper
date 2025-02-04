import os
import json
class Evaluator:
    
    @staticmethod
    def evaluate(responses_path: str):
        files = os.listdir(responses_path)
        dirs = responses_path.split('/')
        dirs.insert(len(dirs)-1, 'insights')
        insights_path = dirs[0]
        for i in range(1, len(dirs)):
             insights_path += '/' + dirs[i]

        insights_path = insights_path + '.txt'
        for labeled_file in files:
            print(labeled_file)
            abs_path = os.path.join(responses_path, labeled_file)
            with open(abs_path, 'r') as file:
                content_file = file.read()
                labeled_data_dict = json.loads(content_file)

                for index in range(len(labeled_data_dict['responses'])):
                    try:
                         data = labeled_data_dict['responses'][index][f'data{index+1}']
                         response = labeled_data_dict['responses'][index][f'response{index+1}']['scraped_data']
                    except Exception as e:
                         return
                    comparisson_result, tp = Evaluator.__compare__(data, response)
                    
                    if response != []:
                              response_length = len(list(response[0].keys())) * len(response)
                              data_length = len(list(data[0].keys())) * len(data)
                    else: continue
                    fp = response_length - tp
                    fn = data_length - tp

                    with open(insights_path, 'a') as insights_file:
                         insights_file.write(f'{labeled_file} query{index+1}: {comparisson_result} -- {tp} -- {fp} -- {fn}\n')



                 
                
    @staticmethod
    def __compare__(expected_responses: list[dict], responses: list[dict]):
        tp = 0
        is_equal = True
        for expected_response in expected_responses:
                for value in list(expected_response.values()):
                     if not Evaluator.__find__(value, responses):
                          is_equal = False
                     else:
                          tp+=1
     #    print(tp)
        return is_equal, tp
                     

    @staticmethod
    def __find__(expected_value, responses: list[dict]):
        for response in responses:
             for value in list(response.values()):
               #    print(value)
                  if expected_value == value:
                       return True     
        return False
    

    def accurancy():
         pass
         

# buscar si hay una biblioteca que te de algo como sinonimos o algo asi, quizas una biblioteca de embedding 


# p = 'code/results/bbc/llama3.3-70B/with_refinement_and_cot'

# Evaluator.evaluate(p)