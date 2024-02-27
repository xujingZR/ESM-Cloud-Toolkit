# ESM Cloud Toolkit

---

## About ESM Cloud Toolkit

A toolkit used for efficient archiving, post-processing and reutilization of scientific research data in energy storage materials. 

一个用于实现科研数据高效管理、后处理以及再利用的工具箱。

---

## Features

**ESM Cloud Toolkit**的整体功能可以分为三个部分：

- **计算数据收集及后处理**
    - 第一性原理计算数据的自动收集及归档至MatElab
    - ……
- **实验数据收集及后处理**
    - 交流阻抗数据一键处理
    - 电化学循环数据一键处理
    - 自动生成演示文稿
    - ……
- **机器学习应用**
    - 针对结构生成指定描述符（当前版本支持SOAP[1]及ACSF[2]等）
    - 训练预测材料性能的机器学习模型
    - 调用模型对未知材料进行预测
    - 微调机器学习势函数（当前版本支持CHGNet[3]）
    - ……

需要注意的是，目前ESM Cloud Toolkit作为后端，将所有的数据、参数设置以及结构都以【记录】的形式。

---

## Usage

**MatElab**：MatElab的使用可在注册为用户后参考帮助文档

**ESM Cloud Toolkit**：使用实例参考examples文件夹中的视频及文档

---

## **Cited**

如果您使用ESM Cloud Toolkit，请引用以下文章：

[1] Jing Xu, Ruijuan Xiao, Hong Li. Chin. Phys. Lett. xx, xxxx (2024)

---

## **Reference**

[1] Michael J. Willatt *et al*.  J. Chem. Phys. 150, 154110 (2019)

[2] Jörg Behler. J. Chem. Phys. 134, 074106 (2011)

[3] Boweng Deng *et al*. Nature Machine Intelligence. 5, 1031 (2023)

[4] MatElab website: [https://in.iphy.ac.cn/eln/#/](https://in.iphy.ac.cn/eln/#/)
