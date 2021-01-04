import os, sys, datetime
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID

if __name__ == "__main__":
    print(GUID)



