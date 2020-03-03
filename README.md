# DP3A
Automatic scheduler for NDPPP

### Software Requirements

### Installation

### Automatic calibration
#### Creating and manipulating in the DP5-workflow environment
DP5 allows for creation of a *DP5-lab*, via
```
DP5-tools.py init labname/
```
Inside a DP5-lab, there are three important folders: *measurements*, *models* and *runs*.
Generally speaking, *measurements* contain measurement sets, *models* contain the starting model and *runs* can contain any amount of runs.
However, it is strongly recommended to stick to a single measurement and a single model in a lab.
Inside the DP5-lab, you can create a *run*:
```
DP5-tools.py newrun run1/
```
This makes a run, which is a standalo
