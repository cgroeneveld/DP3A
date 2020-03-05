# DP3A
Automatic scheduler for NDPPP

### Workflow schedule

### Software Requirements

### Installation

### Tutorial
#### Calibrating in the DP5-workflow environment
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
This makes a run, which is a standalone reduction.
There can be several runs within one lab (but you can't run more than one calibration per lab! Need to make this more clear somehow)
Now, inside ``runs/run1/``, there will be a ``parsets`` folder, which contains the parsets that are necessary for NDPPP.
You probably want to check whether or not these are sufficient for your run.
The default values are optimized for 3C295, and may therefore be (wildly) inadequate for other calibrations.
In particular, you want to look at ``imaging.sh`` (which determines what command is run for cleaning/imaging), ``casamask.fits`` (containing a fits mask made in CASA, omitting this file will make wsclean use an automask) and the various ddecal files, which contain the parsets for calibration.
As the calibration steps will probably take the longest amount of time, it is important to carefully assess the default values.
Finally, ``execute`` contains the calibration steps. The following steps are used:
|character|Function|
|---|---|
|m|Predict a model, and populate the MODEL column with model visibilities. Typically, this is the first step you want to do in any reduction|
|p|Phase-only calibration. This corresponds with calibration of only the phases of the XX/YY polarizations (thus, giving you 2 free parameters per antenna)|
|t|TEC-calibration. This refers to a <img src="https://render.githubusercontent.com/render/math?math=\nu^{-2}"> phase dependency. In addition, such a constrain can prevent overfitting on bad initial models.|
|a|TEC+Phase calibration. Basically TEC-calibration with an additional phase calibration run.|
|d|Diagonal calibration. This begins with a single run of Phase-only calibration, and diagonal calibration is computed on the corrected data from the phase calibration. Diagonal calibration has four free parameters, as it allows for both amplitude and phase to change on the XX/YY correlated polarizations.|
|u|Phase-up. This can be used at fields with a small angular size, as the short baselines are not necessary. Phase-ups remove these short baselines, significantly speeding up the calibration process.\

Each character stands for one calibration step, so ``maapppddd`` means:
  * Predict a model
  * Do two iterations of TEC+Phase calibration
  * Then, do three iterations of Phase calibration
  * Finally, do three iterations of Diagonal calibration
  
Finally, you can execute this by running in the root folder of the lab:
```
DP5-tools.py execute runs/run1/
```
#### Compression and archiving
Measurement sets and solution sets can be large in size, sometimes this can become an issue once multiple measurement sets are used at the same time.
For this reason, it can be beneficial to compress the runs afterwards. 
This can be done using:
```
DP5-compress.py -ms measurements/your_measurement_set.ms -r runs/run1/
```
This will create three new directories: one containing all solution sets, one containing the models that were generated during cleaning and one containing the last model and last solution sets (needs to be filled manually!). 
Next, the DATA column of the measurement set is copied and stored in a new measurement set, using the Dysco storagemanager [CITE DYSCO].
The other columns (such as the MODEL_DATA or CORRECTED_DATA column) are discarded, as these can be reconstructed using the data available in the run itself.
Finally, you can tar and compress it manually (e.g. using GZIP). This will reduce a measurement set of around 300 GB to approximately 60 GB, which is a lot easier to store these sets and move them around.
Uncompressing can be done by:
```
DP5-compress.py -d runs/run1
```
This will automatically predict the model and fill the MODEL_DATA column with model visibilities. Additionally, it will apply the solution set that is stored in the run-folder.
