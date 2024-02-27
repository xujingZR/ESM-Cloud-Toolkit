import pandas as pd
import matplotlib.pyplot as plt

def eis(file_path, legend):
    fig, ax = plt.subplots()
    num = 0
    t_legend = []
    for i in file_path:
        with open(i, 'r') as f:
            data = f.readlines()
            for n in range(len(data)):
                if data[n].startswith('Number'):
                    clean_data = data[n:]
                    with open("clean_data.csv", 'w') as f:
                        f.writelines(clean_data)
        
        eis_data = pd.read_csv("clean_data.csv", header=0)
        ax.scatter(eis_data['impedance'], -eis_data['R/Ohm'])
        ax.plot(eis_data['impedance'], -eis_data['R/Ohm'], alpha=0.5, ls='--')

        t_legend.append(legend[num])
        t_legend.append("_")
        num += 1

    ax.set_xlim([0, 150])
    ax.set_ylim([0, 150])
    # 输入latex公式
    ax.set_xlabel(r'$Z^{real}/\Omega$')
    ax.set_ylabel(r'$-Z^{imag}/\Omega$')
    ax.legend(t_legend)

    fig.savefig('eis.png', dpi=300)
    return None
