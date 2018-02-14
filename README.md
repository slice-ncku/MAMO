# MAMO
Macro-Assignment / Micro-Optimization (MAMO) framework

# Usage
```sh
python micro_optimization.py Exp-Data/task.json Exp-Data/levels.json 10 Exp-Data

python micro_mckp.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 5000

python micro_greedy.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 5000

python micro_cp.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 5000

python macro_uniform.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json

python macro_keepup_uniform.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 5000

python macro_keepup_async.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 5000

python macro_gte_threshold.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 500

python macro_gte_threshold_async.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 500

python macro_keepup_uniform.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 1000

python macro_keepup_uniform_async.py Exp-Data/task.json Exp-Data/levels.json Exp-Data/answers.json 10 1000
```
