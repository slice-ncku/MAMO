import os
import sys
import copy
import json
import time
from multiprocessing import Pool

from pprint import pprint
from micro_optimization import THRESHOLD
from micro_greedy import micro_greedy 
from micro_cp import micro_cp
from micro_mckp import micro_mckp

SIMULATE_CNT = 5
MAX_ROUND = 5
CONF_THRESHOLD = 0.3

def macro_gte_threshold_simulate(alg, tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget):
    round_results = list()
    for _ in range(MAX_ROUND):
        round_results.append({
            "round_rev": float(),
            "round_correct": float(),
            "round_remaining": float()
        })

    total_rev = float()
    total_correct = float()
    remaining_budget = budget

    round_tasks = copy.deepcopy(tasks)
    tasks_dict = dict()
    for task in tasks:
        tasks_dict[task['id']] = copy.deepcopy(task)
        tasks_dict[task['id']]['is_solved'] = False

    for round_num in range(MAX_ROUND):
        round_budget = int(remaining_budget/(MAX_ROUND - round_num))

        result_tasks, outcome_dict = alg(round_tasks, levels_dict, \
                    tasks_answer_dict, max_assign_cnt, round_budget)
        next_round_tasks = list()
        for result_task in result_tasks:
            new_confidence = result_task['pre-answer']['confidence']
            pre_confidence = tasks_dict[result_task['id']]['pre-answer']['confidence']
            tasks_dict[result_task['id']]['pre-answer']['confidence'] = new_confidence
            tasks_dict[result_task['id']]['is_solved'] = result_task['is_solved']
            if new_confidence < THRESHOLD and new_confidence >= CONF_THRESHOLD:
                next_round_tasks.append(result_task)
        round_tasks = next_round_tasks

        total_rev += outcome_dict['revenue_sum']
        total_correct += outcome_dict['correct_cnt']
        remaining_budget = remaining_budget - round_budget + outcome_dict['remaining_budget']

        round_results[round_num]['round_rev'] += outcome_dict['revenue_sum']
        round_results[round_num]['round_correct'] += outcome_dict['correct_cnt']
        round_results[round_num]['round_remaining'] += remaining_budget

    simulate_result = {
        "total_rev": total_rev,
        "total_correct": total_correct,
        "remaining_budget": remaining_budget,
        "rounds": round_results
    }
    return simulate_result

def macro_gte_threshold_async(alg, tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget):
    macro_result = {
        "total_rev": float(),
        "total_correct": float(),
        "remaining_budget": float(),
        "rounds": list()
    }
    for round_num in range(MAX_ROUND):
        macro_result['rounds'].append({
            "round_rev": float(),
            "round_correct": float(),
            "round_remaining": float()
        })

    pool = Pool(processes=5)
    simulate_processes = list()

    for i in range(SIMULATE_CNT):
        print(i)
        simulate_processes.append(
            pool.apply_async(
                macro_gte_threshold_simulate,
                (alg, tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget, )
            )
        )

    pool.close()
    pool.join()

    for simulate_process in simulate_processes:
        simulate_result = simulate_process.get()
        macro_result['total_rev'] += simulate_result['total_rev']
        macro_result['total_correct'] += simulate_result['total_correct']
        macro_result['remaining_budget'] += simulate_result['remaining_budget']

        for round_num in range(MAX_ROUND):
            macro_result['rounds'][round_num]['round_rev'] += \
                simulate_result['rounds'][round_num]['round_rev']
            macro_result['rounds'][round_num]['round_correct'] += \
                simulate_result['rounds'][round_num]['round_correct']
            macro_result['rounds'][round_num]['round_remaining'] += \
                simulate_result['rounds'][round_num]['round_remaining']

    macro_result['total_rev'] = macro_result['total_rev'] / SIMULATE_CNT
    macro_result['total_correct'] = macro_result['total_correct'] / SIMULATE_CNT
    macro_result['remaining_budget'] = macro_result['remaining_budget'] / SIMULATE_CNT
    for round_num in range(MAX_ROUND):
        macro_result['rounds'][round_num]['round_rev'] = \
            macro_result['rounds'][round_num]['round_rev'] / SIMULATE_CNT
        macro_result['rounds'][round_num]['round_correct'] = \
            macro_result['rounds'][round_num]['round_correct'] / SIMULATE_CNT
        macro_result['rounds'][round_num]['round_remaining'] = \
            macro_result['rounds'][round_num]['round_remaining'] / SIMULATE_CNT
    return macro_result

if __name__ == "__main__":
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

    start_time = time.time()
    macro_result = macro_gte_threshold_async(micro_mckp, tasks, levels_dict, tasks_answer_dict, max_assign_cnt, budget)
    print(time.time() - start_time)
    pprint(macro_result)
