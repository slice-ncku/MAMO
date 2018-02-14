import os
import sys
import json
import random
import numpy as np


ALPHA = 0.8
MAX_ITERATION = 100
THRESHOLD = 0.75

def gen_difficulty(task):
    """
    利用機率的方法決定 difficulty，把 pre-confidence 的左邊跟右邊個切三段，當作標準差，
    並在左右邊各用不同的標準差隨機 Random 出 200 個數值，在 pre-confidence 的左右邊各取 50 個數值，
    最後在 100 個數值內隨機挑選出一個當作 difficulty。
    Args:
        task (dict): 有 task 資訊的 dictonary ，可參考 Exp-Data/task.json

    Return:
        float: 0 ~ 1 之間的浮點數。
    """
    pre_confidence = task['pre-answer']['confidence']
    difficulty_std_r = (1 - pre_confidence) / 3
    difficulty_std_l = pre_confidence / 3
    difficulty_list = list()

    difficulty_2d_r = (pre_confidence + difficulty_std_r * np.random.randn(1, 200))
    difficulty_2d_l = (pre_confidence + difficulty_std_l * np.random.randn(1, 200))
    for difficulty in difficulty_2d_r[0]:
        if difficulty >= pre_confidence and difficulty <= 1:
            difficulty_list.append(difficulty)

        if len(difficulty_list) == 50:
            break

    for difficulty in difficulty_2d_l[0]:
        if difficulty >= 0 and difficulty <= pre_confidence:
            difficulty_list.append(difficulty)

        if len(difficulty_list) == 100:
            break

    difficulty = difficulty_list[random.randint(0, 99)]
    return difficulty

def gen_true_conf(pre_confidence, level_comb, levels_dict, answer_dict):
    """
    利用 pre_confidence 以及 level_comb ，計算出在 level_comb 的組合下，
    最後得到的 confidence 會是多少。

    Args:
        pre_confidence (float): 0 ~ 1 之間的浮點數
        level_comb (list): worker 的組合，像是 ['level1', 'level1', 'level2'] 代表兩個 level 1 的 worker ，以及一個 level 2 的 worker
        levels_dict (dict): worker 的等級，以及 quality ，可以參考 Exp-Data/levels.json
        answer_dict (dict): 在真正的 Crowdsourcing 中， level1 及 level2 worker 的回答，可參考 Exp-Data/answers.json

    Return:
        float: 0 ~ 1 之間的浮點數
    """
    true_conf_direct = pre_confidence
    false_conf_direct = 1 - true_conf_direct
    for level_name in level_comb:
        random_answer_index = random.randint(0, len(answer_dict[level_name])-1)
        answer = answer_dict[level_name][random_answer_index]
        if answer['option'] is True:
            true_conf_direct = true_conf_direct * levels_dict[level_name]['quality']
            false_conf_direct = false_conf_direct * (1 - levels_dict[level_name]['quality'])
        else:
            true_conf_direct = true_conf_direct * (1 - levels_dict[level_name]['quality'])
            false_conf_direct = false_conf_direct * levels_dict[level_name]['quality']
    true_conf = true_conf_direct / (true_conf_direct + false_conf_direct)
    return true_conf

def micro_optimization(task, levels_dict, max_assign_cnt):
    """
    計算 task 在有作多能指派多少 worker 的數量限制下，每一種 worker 組合能得到的 revenue 期望值各是多少。

    Args:
        task (dict): 有 task 資訊的 dictonary ，可參考 Exp-Data/task.json.
        levels_dict (dict): worker 的等級，以及 quality ，可以參考 Exp-Data/levels.json
        max_assign_cnt (int): 最多能指派多少 worker

    Return:
        list of dictionary: 每一個 dictionary 都包含 level_comb, gte_threshold_cnt, expected_revenue 以及 cost
    """
    difficulty = gen_difficulty(task)
    levels_dict['level1']['true_ratio'] = \
        ALPHA * levels_dict['level1']['quality'] + (1 - ALPHA) * difficulty
    levels_dict['level2']['true_ratio'] = \
        ALPHA * levels_dict['level2']['quality'] + (1 - ALPHA) * difficulty

    level1_max_assign_cnt = len(task['answers']['level1'])
    level2_max_assign_cnt = len(task['answers']['level2'])
    level_combs = list()
    for total_assign_cnt in range(1, max_assign_cnt + 1):
        for level1_assign_cnt in range(total_assign_cnt+1):
            level2_assign_cnt = total_assign_cnt - level1_assign_cnt
            if level1_assign_cnt > level1_max_assign_cnt or \
                level2_assign_cnt > level2_max_assign_cnt:
                continue
            level_comb = level1_assign_cnt * ['level1'] + level2_assign_cnt * ['level2']
            level_combs.append(level_comb)

    results = list()
    for level_comb in level_combs:
        gte_threshold_cnt = int()
        cost_sum = int()
        for level_name in level_comb:
            cost_sum += levels_dict[level_name]['cost']

        for i in range(MAX_ITERATION):
            true_conf_direct = task['pre-answer']['confidence']
            false_conf_direct = 1 - true_conf_direct

            for level_name in level_comb:
                true_ratio = levels_dict[level_name]['true_ratio']
                random_float = random.uniform(0, 1)
                if random_float <= true_ratio:
                    true_conf_direct = true_conf_direct * levels_dict[level_name]['quality']
                    false_conf_direct = false_conf_direct * (1 - levels_dict[level_name]['quality'])
                else:
                    true_conf_direct = true_conf_direct * (1 - levels_dict[level_name]['quality'])
                    false_conf_direct = false_conf_direct * levels_dict[level_name]['quality']

            true_conf = true_conf_direct / (true_conf_direct + false_conf_direct)
            if true_conf >= THRESHOLD:
                gte_threshold_cnt += 1

        expected_revenue = gte_threshold_cnt / MAX_ITERATION * task['revenue']
        result_dict = {
            "level_comb": level_comb,
            "gte_threshold_cnt": gte_threshold_cnt,
            "expected_revenue": expected_revenue,
            "cost": cost_sum
        }
        results.append(result_dict)
    return results

if __name__ == '__main__':
    task_file_path = sys.argv[1]
    worker_file_path = sys.argv[2]
    max_assign_cnt = int(sys.argv[3])
    dest_file_path = sys.argv[4]

    with open(task_file_path, "r") as myfile:
        tasks = json.load(myfile)

    with open(worker_file_path, "r") as myfile:
        levels_dict = json.load(myfile)

    output_list = list()
    for task in tasks:
        results = micro_optimization(task, levels_dict, max_assign_cnt)

        output_dict = {
            "task_id": task['id'],
            "pre_confidence": task['pre-answer']['confidence'],
            "revenue": task['revenue'],
            "results": results
        }
        output_list.append(output_dict)

    with open(os.path.join(dest_file_path, "micro_optimization_%d.json") % (max_assign_cnt), "w") as fd:
        json.dump(output_list, fd, indent=4)
