import sys
import json
from pprint import pprint

from micro_optimization import THRESHOLD, micro_optimization, gen_true_conf


def micro_greedy(tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget):
    """
    先將 task 做 revenue 由高而低的排列，從 revenue 最大的 task 開始解。

    Args:
        tasks (list): 有 task 資訊的 dictonary ，可參考 Exp-Data/task.json.
        levels_dict (dict): worker 的等級，以及 quality ，可以參考 Exp-Data/levels.json
        tasks_answer_dict (dict): 在真正的 Crowdsourcing 中， level1 及 level2 worker 的回答，可參考 Exp-Data/answers.json
        max_assign_cnt (int): 最多能指派多少 worker
        budget (int): 預算

    Return:
        tasks (list): 會將每個 task 新增一個 is_solved 的值，如果已經被解掉的 task ， is_solved=True
        output_dict (dict): 包含 revenue_sum, correct_cnt 以及 remaining_budget
    """
    remaining_budget = budget
    revenue_sum = int()
    correct_cnt = int()

    for task in tasks:
        task['is_solved'] = False

    tasks_order_by_revenue = sorted(tasks, key=lambda k: k['revenue'], reverse=True)
    for task in tasks_order_by_revenue:
        task_id = task['id']
        pre_confidence = task['pre-answer']['confidence']

        results = micro_optimization(task, levels_dict, max_assign_cnt)
        results_order_by_cost = sorted(results, key=lambda k: k['cost'])
        results_order_by_expected_revenue = sorted(results_order_by_cost, \
                                                key=lambda k: k['expected_revenue'], reverse=True)
        for result in results_order_by_expected_revenue:
            if (remaining_budget - result['cost']) < 0:
                continue

            if result['expected_revenue'] == 0:
                continue

            true_conf = gen_true_conf(pre_confidence, result['level_comb'], \
                            levels_dict, tasks_answer_dict[task_id])
            task['pre-answer']['confidence'] = true_conf

            if true_conf >= THRESHOLD:
                revenue_sum += task['revenue']
                correct_cnt += 1
                task['is_solved'] = True

            remaining_budget -= result['cost']
            break

    outcome_dict = {
        'revenue_sum': revenue_sum,
        'correct_cnt': correct_cnt,
        'remaining_budget': remaining_budget
    }
    return tasks, outcome_dict


if __name__ == '__main__':
    task_file_path = sys.argv[1]
    worker_file_path = sys.argv[2]
    answer_file_path = sys.argv[3]
    max_assign_cnt = int(sys.argv[4])
    budget = int(sys.argv[5])

    with open(task_file_path, "r") as myfile:
        tasks = json.load(myfile)

    with open(worker_file_path, "r") as myfile:
        levels_dict = json.load(myfile)

    with open(answer_file_path, "r") as myfile:
        tasks_answer_dict = json.load(myfile)

    new_tasks, outcome_dict = micro_greedy(tasks, levels_dict, \
                                tasks_answer_dict, max_assign_cnt, budget)

    pprint(outcome_dict)
