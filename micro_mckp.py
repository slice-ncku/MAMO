import sys
import copy
import json
from pprint import pprint

from micro_optimization import THRESHOLD, micro_optimization, gen_true_conf


def micro_mckp(tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget):
    """
    將我們的問題套用到多背背問題後的解法，可以參考 http://www2.lssh.tp.edu.tw/~hlf/class-1/lang-c/DP.pdf ，裡面的「P06: 分組的背包問題」。

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
    for task in tasks:
        task['is_solved'] = False

    budget_expected_revenue = [0] * (budget+1)
    budget_expected_correct = [0] * (budget+1)
    budget_do_tasks = list()
    for tmp_budget in range(budget+1):
        budget_do_tasks.append(dict())

    for task in tasks:
        task_id = task['id']
        results = micro_optimization(task, levels_dict, max_assign_cnt)
        # task['results'] = results

        for tmp_budget in range(budget, 0, -1):
            for result in results:
                cost = result['cost']
                expected_revenue = result['expected_revenue']

                if tmp_budget - cost < 0:
                    continue

                if expected_revenue == 0:
                    continue

                if budget_expected_revenue[tmp_budget - cost] + expected_revenue > \
                        budget_expected_revenue[tmp_budget]:

                    budget_expected_revenue[tmp_budget] = \
                        budget_expected_revenue[tmp_budget - cost] + expected_revenue
                    budget_expected_correct[tmp_budget] = \
                        budget_expected_correct[tmp_budget - cost] + 1

                    budget_do_tasks[tmp_budget - cost][task_id] = {
                        "level_comb": result['level_comb']
                    }
                    budget_do_tasks[tmp_budget] = copy.deepcopy(budget_do_tasks[tmp_budget - cost])


    revenue_sum = int()
    correct_cnt = int()
    best_budget = budget_expected_revenue.index(max(budget_expected_revenue))
    for task in tasks:
        if budget_do_tasks[best_budget].get(task['id']) is None:
            continue
        task_id = task['id']
        pre_confidence = task['pre-answer']['confidence']
        level_comb = budget_do_tasks[best_budget][task['id']]['level_comb']
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
        'remaining_budget': budget - best_budget
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

    tasks, outcome_dict = micro_mckp(tasks, levels_dict, \
                                tasks_answer_dict, max_assign_cnt, budget)
    pprint(outcome_dict)
    # pprint (tasks)
