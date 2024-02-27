import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def read_data(data_path):
    with open(data_path, 'rb') as f:
        data = f.readlines()
    data = [str(i, encoding='gbk').split(sep=",") for i in data]
    return data

def get_cycles_data(data):
    n_cycle = 0
    cycles = {}
    for i in data[:]:
        if i[0] == "循环序号":
            n_cycle += 1
            cycles[n_cycle] = [i]
        else:
            cycles[n_cycle].append(i)
    return cycles

def get_charge_discharge_per_cycle(cycles, target_idx):
    t_cycle = cycles[target_idx]
    steps = {}
    n_step = 0
    for i in range(2, len(t_cycle)):
        if t_cycle[i][0] == "工步序号":
            n_step = i
            steps[t_cycle[n_step+1][1]] = [t_cycle[i]]
        else:
            steps[t_cycle[n_step+1][1]].append(t_cycle[i])
            
    charge = pd.DataFrame(np.array(steps["倍率充电"][2:]))
    charge.columns = charge.iloc[0]
    charge = charge.iloc[1:]
    discharge = pd.DataFrame(np.array(steps["倍率放电"][2:]))
    discharge.columns = discharge.iloc[0]
    discharge = discharge.iloc[1:]
    charge_v = charge["电压(V)"]
    discharge_v = discharge["电压(V)"]

    v_capacity = [
        charge_v.to_numpy(dtype=float), 
        charge["比容量(mAh/g)"].to_numpy(dtype=float), 
        discharge_v.to_numpy(dtype=float), 
        discharge["比容量(mAh/g)"].to_numpy(dtype=float)
    ]
    return v_capacity

def plot_capacity_v(v_capacity, legend, compare=False):

    # plot figure
    nested = False
    plt.figure()
    if isinstance(v_capacity[0],list):
        nested = True
        for i in range(len(v_capacity)):
            plt.plot(v_capacity[i][1], v_capacity[i][0], c = 'C'+str(i))
            plt.plot(v_capacity[i][3], v_capacity[i][2], c = 'C'+str(i))

    else:
        plt.plot(v_capacity[1], v_capacity[0], c='C0')
        plt.plot(v_capacity[3], v_capacity[2], c='C0')

    plt.xlabel("Capacity mAh/g")
    plt.ylabel("Voltage V")

    # plot legend
    if compare == False:
        if nested == True and len(v_capacity)<10:
            legends = []
            for i in range(len(v_capacity)):
                    legends.append(legend[i])
                    legends.append("_")
            plt.legend(legends)
        else:
            pass
    else:
        if nested == True and len(v_capacity)<10:
            legends = []
        else:
            pass
    else:
        if nested == True and len(v_capacity)<10:
            legends = []
            for i in range(len(v_capacity)):
                    legends.append(legend[i])
                    legends.append("_")
            plt.legend(legends)

    plt.savefig("capacity_vs_voltage.png", dpi=300)

def get_n_cycles_vs_capacity(cycles):
    discharge_specific_capacities = []
    charge_specific_capacities = []
    coulombic_efficiencies = []
    for i in cycles.keys():
        cycle_infor = pd.DataFrame(np.array(cycles[i][:2]))
        cycle_infor.columns = cycle_infor.iloc[0]
        cycle_infor = cycle_infor[1:]
        discharge_specific_capacities.append(cycle_infor["放电比容量(mAh/g)"].to_numpy(dtype=float)[0])
        charge_specific_capacities.append(cycle_infor["充电比容量(mAh/g)"].to_numpy(dtype=float)[0])
        coulombic_efficiencies.append(cycle_infor["效率(%)"].to_numpy(dtype=float)[0])
    
    return charge_specific_capacities, discharge_specific_capacities, coulombic_efficiencies

def main_func(files_path, t_cycle, legend):

    if len(files_path) == 1:
        legend = [f"Cycles_{i+1}" for i in range(t_cycle)]
        compare_flag = False
        data = read_data(files_path[0])
        cycles = get_cycles_data(data)
        xs = []
        for i in range(1, t_cycle+1):
            x = get_charge_discharge_per_cycle(cycles, i)
            xs.append(x)
        
        plot_capacity_v(xs, legend, compare=compare_flag)

        charge_specific_capacities, discharge_specific_capacities, coulombic_efficiencies = get_n_cycles_vs_capacity(cycles)
        fig, ax1 = plt.subplots()
        ax1.plot(cycles.keys(), charge_specific_capacities)
        ax1.set_xlabel("Cycles")
        ax1.set_ylabel("Capacity mAh/g")
        ax1.legend([f"ICE : {coulombic_efficiencies[0]}%"])

        ax2 = ax1.twinx()
        ax2.set_ylim(0, 100)
        ax2.plot(cycles.keys(), coulombic_efficiencies, alpha=0.5)
        ax2.set_ylabel("Coulombic Efficiencies %")
        fig.savefig("capacity_vs_cycles.png", dpi=300)

        
    elif len(files_path) > 1:
        compare_flag = True
        xs = []
        cycles_es = []
        for path in files_path:
            data = read_data(path)
            cycles = get_cycles_data(data)
            cycles_es.append(cycles)
            x = get_charge_discharge_per_cycle(cycles, 1)
            xs.append(x)
        
        plot_capacity_v(xs, legend, compare=compare_flag)

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax2.set_ylim(0, 100)
        for cycles in cycles_es:
            charge_specific_capacities, discharge_specific_capacities, coulombic_efficiencies = get_n_cycles_vs_capacity(cycles)
            ax1.scatter(cycles.keys(), charge_specific_capacities, marker=".")
            ax2.plot(cycles.keys(), coulombic_efficiencies, alpha=0.5)

        ax1.legend(legend, loc="lower left")
        ax1.set_xlabel("Cycles")
        ax1.set_ylabel("Capacity mAh/g")
        ax2.set_ylabel("Coulombic Efficiencies %")
        fig.savefig("capacity_vs_cycles.png", dpi=300)

    else:
        print("Please input the file")

return None
