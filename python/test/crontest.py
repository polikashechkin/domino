import os, sys, datetime

python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.jobs import Job 

if __name__ == "__main__":
    UUID = sys.argv[1]
    with Job('domino', name = '', description = '', uuid = UUID) as job:
        print('Привет') 

print(UUID)
