import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use("bmh")
font = {'size': 13}
matplotlib.rc('font', **font)

entries = [
    ("O\n(12 N, 16 E)", 5.83),
    ("S\n(21 N, 25 E)", 3.91),
    ("M\n(29 N, 34 E)", 2.43),
    ("O+S\n(33 N, 41 E)", 8.16),
    ("O+M\n(41 N, 50 E)", 3.86),
    ("M+S\n(50 N, 59 E)", 9.40),
    ("O+M+S\n(62 N, 75 E)", 9.66),
]

entries.reverse()
labels, ttc = zip(*entries)
print(labels)
print(ttc)

plt.figure(figsize=(5, 4))
bars = plt.barh(labels, ttc)
plt.xlabel("Time-to-Completion (s)")
plt.ylabel("Benchmark Combination")
plt.tight_layout()
plt.savefig("ttc.pdf", bbox_inches='tight', pad_inches=0)
plt.show()
