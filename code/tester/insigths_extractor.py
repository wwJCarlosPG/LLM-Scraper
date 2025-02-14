# path = 'code/results/amazon_best_sellers/llama3.3-70B/insights/'
techniques = ['with_separated_selfconsistency', 'with_selfconsistency', 'with_refinement_and_cot', 'without_refinement_with_cot']
# techniques = ['without_cot']
sites = ['amazon_best_sellers']
# 'dobby-mini-leashed-llama3.1-8B'
models = ['dobby-mini-leashed-llama3.1-8B']
# 
#'dobby-mini-leashed-llama3.1-8B', 
# TOTAL = 0
# TRUES = 0
# total = 0
# trues = 0
# falses = 0
with_separrated_selfconsistency = {'name': 'with_separrated_selfconsistency', 'tp': 0, 'fp': 0, 'fn': 0, 'total': 0, 'responses':0, 'accurancy':'0'}
with_selfconsistency = {'name': 'with_selfconsistency' ,'tp': 0, 'fp': 0, 'fn': 0, 'total': 0, 'responses':0, 'accurancy':'0'}
with_refinement_and_cot = {'name': 'with_refinement_and_cot','tp': 0, 'fp': 0, 'fn': 0, 'total': 0, 'responses':0, 'accurancy':'0'}
without_refinement_with_cot = {'name': 'without_refinement_with_cot', 'tp': 0, 'fp': 0, 'fn': 0, 'total': 0, 'responses': 0, 'accurancy':'0'}
# without_cot = {'name': 'without_cot', 'tp': 0, 'fp': 0, 'fn': 0, 'total': 0, 'responses': 0, 'accurancy':'0'}
robs = []
techs = [with_separrated_selfconsistency, with_selfconsistency, with_refinement_and_cot, without_refinement_with_cot]
# techs = [without_cot]
rob=0
rob2 = 0
robs2 = []
for i in range(len(techniques)):
    for site in sites:
        for model in models:
            path = f'code/results/{site}/{model}/insights/'
            with open(f'{path}{techniques[i]}.txt', 'r') as file:
                # print("Technique: ", techniques[i])
                stat = file.read()
                
                m = 0
                stat = stat.strip().split('\n')
                techs[i]['total'] = len(stat)
                
                
                stat = [s.split('--') for s in stat]
                
                r = 0
                
                for s in stat:
                    # print(s[0])
                    # print(s[0].startswith('amazon'))
                    if s[0].startswith('amazon') and s[0].split(':')[1].strip() == 'True':
                        # print('True')
                        for s2 in stat:
                            # print(s2[0][5:].strip())
                            # print(f'S2[0][4:] -> {s2[0][4:].strip()}')
                            # print(f'S[0][4:] -> {s2[0][4:].strip()}')

                            if s2[0].startswith('div') and s2[0][4:].split(':')[0].strip() == s[0].split(':')[0]:
                                # print(s2[0][4:].strip())

                               
                                if s2[0].split(':')[1].strip() == 'True':
                                    # print('div')
                                    rob +=1
                            
                            elif s2[0].startswith('attr') and s2[0][5:].split(':')[0].strip() == s[0].split(':')[0]:
                                if s2[0].split(':')[1].strip() == 'True':
                                    # print('attr')
                                    rob +=1
                                
                    elif s[0].startswith('bbc') and s[0].split(':')[1].strip() == 'True':
                        # print('True')
                        for s2 in stat:
                            if s2[0].startswith('div') and s2[0][4:].split(':')[0].strip() == s[0].split(':')[0]:
                                # print(s2[0][4:].strip())

                               
                                if s2[0].split(':')[1].strip() == 'True':
                                    # print('div')
                                    rob2 +=1
                            
                            elif s2[0].startswith('attr') and s2[0][5:].split(':')[0].strip() == s[0].split(':')[0]:
                                if s2[0].split(':')[1].strip() == 'True':
                                    # print('attr')
                                    rob2 +=1

                    techs[i]['tp'] += int(s[1].strip())
                    techs[i]['fp'] += int(s[2].strip())
                    techs[i]['fn'] += int(s[3].strip())
                    techs[i]['responses'] += float(s[6].strip())
                

                    # print(s)
                    if s[0].split(':')[1].strip() == 'True':
                        m+=1
            
            robs2.append(rob2)
            robs.append(rob)
            # print(f'rob: {rob}')
            rob = 0
            rbo2 = 0
            techs[i]['accurancy'] = m/techs[i]['total']
                # print(f"True: {m}")
                # trues+=m
                # techs[i]['tp'] = trues
                # print(f"False: {r}\n")
                # falses+=r


# print(total)
# print(trues)
# print(falses)
# print(len(stat))
print(f'rob with separrated selfconsistency: {robs[0]/techs[0]["total"]}')
print(f'rob with selfconsistency: {robs[1]/techs[1]["total"]}')
print(f'rob with refinement and cot: {robs[2]/techs[2]["total"]}')
print(f'rob without refinement with cot: {robs[3]/techs[3]["total"]}')
# print(techs[0]['total'] + techs[1]['total'] + techs[2]['total'] + techs[3]['total'])
# print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
print(f'rob with separrated selfconsistency: {robs2[0]/techs[0]["total"]}')
print(f'rob with selfconsistency: {robs2[1]/techs[1]["total"]}')
print(f'rob with refinement and cot: {robs2[2]/techs[2]["total"]}')
print(f'rob without refinement with cot: {robs2[3]/techs[3]["total"]}')
# print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')


# print(techs[0]['total'] + techs[1]['total'] + techs[2]['total'] + techs[3]['total'])
# print(techs)
# # 13.85 %
for t in techs:
    # t['tp'] = t['tp']/2
    # t['fp'] = t['fp']/2
    # t['fn'] = t['fn']/2
    # t['total'] = t['total']/2
    # t['responses'] = t['responses']/2

    tp = t['tp']/t['total']
    fp = t['fp']/t['total']
    fn = t['fn']/t['total']
    recall = tp / (tp + fn)
    prec = tp / (tp + fp)
    responses = t['responses']/t['total']
    f1 = 2 * prec*recall / (prec + recall)
    print(f"Technique: {t['name']}: {responses}\n")



# prec = tp / (tp + fp)
