"""
Genesis produces candidates/gen*, cost.txt, and cover.txt. But during running, it requires a space.txt.
"""

import sys
import os

trained_space_dir = sys.argv[1]

cnt = 0
for root, dirs, files in os.walk(trained_space_dir + "/candidate/"):
    for file in files:
        if not file.endswith(".po") and not file.startswith("gen"):
            continue
        cnt += 1


with open(trained_space_dir +'/space.txt', 'w+') as outfile:
    outfile.write(str(cnt) + ' ')
    for i in range(cnt):
        outfile.write(str(i) + ' ')
