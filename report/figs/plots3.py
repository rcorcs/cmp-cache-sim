
import matplotlib.pyplot as plt
import numpy as np

plt.clf()
maxy = 0

ys = {}
ys[32] = 3.3812306722
ys[64] = 3.37538146973
ys[128] = 3.37238057454
ys[256] = 3.37238057454
ys[512] = 3.37238057454
ys[1024] = 3.21384175618
ys[2048] = 3.21114603678
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Trace 1')
maxy = max(maxy,max(ys.values()))

ys = {}
ys[32] = 4.170295859
ys[64] = 4.16985031402
ys[128] = 4.16914772386
ys[256] = 4.16798245238
ys[512] = 4.16722845319
ys[1024] = 4.16722845319
ys[2048] = 4.16722845319
plt.plot(sorted(ys.keys()), [ys[k] for k in sorted(ys.keys())],linewidth=2,marker='o',label='Trace 2')
maxy = max(maxy,max(ys.values()))

maxy *= 1.1

plt.xlabel('Number of Cache Lines in Cache L2')
plt.ylabel('Average Number of Cycles Per Request')
plt.xlim(0,max(ys.keys()))
plt.ylim(0,maxy)
plt.xticks([64,256,512,1024,2048])
plt.legend(loc='best')
#plt.show()
plt.savefig('fig-3.pdf')

