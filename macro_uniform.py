import sys
import json
from pprint import pprint

from micro_optimization import THRESHOLD, micro_optimization, gen_true_conf


def macro_uniform(tasks, levels_dict, tasks_answer_dict, level_comb):
    """
    將每一個 task 都分配一樣的 worker 組合

    Args:
        tasks (list): 有 task 資訊的 dictonary ，可參考 Exp-Data/task.json.
        levels_dict (dict): worker 的等級，以及 quality ，可以參考 Exp-Data/levels.json
        tasks_answer_dict (dict): 在真正的 Crowdsourcing 中， level1 及 level2 worker 的回答，可參考 Exp-Data/answers.json
        level_comb (list): worker 的組合，像是 ['level1', 'level1', 'level2'] 代表兩個 level 1 的 worker ，以及一個 level 2 的 worker
    Return:
        tasks (list): 會將每個 task 新增一個 is_solved 的值，如果已經被解掉的 task ， is_solved=True
        output_dict (dict): 包含 revenue_sum, correct_cnt 以及 remaining_budget
    """
    revenue_sum = int()
    correct_cnt = int()

    for task in tasks:
        task['is_solved'] = False
        task['origin_exp_revenue'] = task['pre-answer']['confidence'] * task['revenue']

    tasks_order_by_origin_exp_revenue = sorted(tasks, \
                            key=lambda k: k['origin_exp_revenue'], reverse=True)
    for task in tasks_order_by_origin_exp_revenue:
        task_id = task['id']
        pre_confidence = task['pre-answer']['confidence']

        true_conf = gen_true_conf(pre_confidence, level_comb, \
                            levels_dict, tasks_answer_dict[task_id])
        task['pre-answer']['confidence'] = true_conf

        if true_conf >= THRESHOLD:
            revenue_sum += task['revenue']
            correct_cnt += 1
            task['is_solved'] = True

    outcome_dict = {
        'revenue_sum': revenue_sum,
        'correct_cnt': correct_cnt,
        'remaining_budget': 0
    }
    return tasks, outcome_dict


if __name__ == '__main__':
    task_file_path = sys.argv[1]
    worker_file_path = sys.argv[2]
    answer_file_path = sys.argv[3]

    with open(task_file_path, "r") as myfile:
        tasks = json.load(myfile)

    with open(worker_file_path, "r") as myfile:
        levels_dict = json.load(myfile)

    with open(answer_file_path, "r") as myfile:
        tasks_answer_dict = json.load(myfile)

    level_comb = ["level1"]

    new_tasks, outcome_dict = macro_uniform(tasks, levels_dict, \
                                tasks_answer_dict, level_comb)

    pprint(outcome_dict)
