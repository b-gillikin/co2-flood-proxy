# Predecessor Notes

Structured notes for PW-1 in `chapter-prework/June 2026 - How-To.docx`.

Sources read:

- Jan-Philipp Viefhues, 2022, `chapter-prework/Jan_Philip_IDnr6258161_TIP%20Master%20Thesis.pdf`
- S. Eryilmaz, 2025, `chapter-prework/Eryilmaz-2025.pdf`

Extraction note: both PDFs were read from local source files using Python PDF text extraction. Some figures/tables rendered imperfectly in extracted text, but the prose, methods, key variables, and reported metrics were usable.

## Executive Read

The two predecessors establish the Kerkrade calibration site as a real mine-gas signal setting, but neither does the chapter's proposed work.

Viefhues (2022) establishes the flood-linked CO2 mechanism at the Kerkrade house during the July 2021 flood. It shows that CO2 leakage frequency and concentration increased during and shortly after the flood, and that pressure, humidity, Rhine water, groundwater, and mine water matter in different ways across before/during/after-flood periods. It also builds Random Forest classifiers for CO2 leakage and flood-period classification. Its strongest inheritance for this chapter is the physical and empirical premise: the site responds to flooding and hydrological state, and mine/groundwater variables are important.

Eryilmaz (2025) establishes the feature-substitution premise on a normal-period window: basement CO2 leak events can be predicted using outdoor weather-station variables nearly as well as using indoor IoT variables. Its strongest inheritance for this chapter is not "CO2 ablation" or transfer. It is same-site feature substitution: external meteorological features predict the same indoor basement CO2 target at nearly the same AUROC as indoor features.

This chapter should not merely rerun either predecessor. The step beyond is to use the longer 2025-present stream to characterize the continuous multivariate signal, explicitly decompose barometric and hydrological contributions, build soft hydrological labels from current discharge data, and test whether any learned signal travels beyond the single Kerkrade calibration site.

## Viefhues 2022

### Citation / Identity

Jan-Philipp Ludger Maria Viefhues. 2022. "Prediction of CO2 leakage and flood using machine learning models: A data driven approach in the historic coal mining district in the province of Limburg (Kerkrade)." Master's thesis, Maastricht University / sustainably.io. Dated January 11, 2022.

### Central Purpose

Viefhues asks two connected questions:

- What effect did the July 2021 flood catastrophe have on CO2 concentrations and air quality in houses above closed mine shafts in Kerkrade?
- What factors drove elevated CO2 before, during, and after the flood, and can flood-driving indicators support an early-warning model?

The thesis has two analytical strands: first, a descriptive and ML-assisted analysis of flood effects on CO2 leakage; second, a Random Forest flood-classification model intended as a foundation for warning-system thinking.

### Data Window

- Main IoT window: August 25, 2020 to September 1, 2021.
- Flood-period construction:
  - First substantial precipitation: June 29, 2021.
  - Main peak: July 14-15, 2021.
  - Flood end approximated around July 18, 2021 based on flattening water levels.
- Data are divided into before, during, and after-flood periods.
- IoT readings were originally minute-level and aggregated to hourly resolution.

### Data Sources

Core source:

- Sustainably.io IoT sensors in a Kerkrade house above a closed mine shaft.

IoT variables:

- CO2
- Temperature
- Humidity
- Atmospheric pressure
- PM10
- PM2.5

External variables:

- Precipitation from DWD Aachen-Orsbach.
- Rhine water level from the German Federal Institute of Hydrology.
- Stream water level and discharge from Waterstand Limburg.
- Groundwater and mine-water level data obtained through Jean Hacking / Province of Limburg and Rene Mols / Waterschap Limburg.

Viefhues notes that groundwater and mine-water values were relative to surface level, so smaller values represent higher absolute water levels. Daily ground/mine-water observations were converted to hourly scale to align with the rest of the dataset.

### Data Preparation

Important details to inherit:

- IoT data were cleaned, typed, converted to a time-series object, and aggregated from minute-level to hourly.
- Missing values from connection interruptions were deleted.
- Outliers were removed except CO2 outliers, because CO2 peaks are the signal of interest.
- One sensor had ABC autocalibration enabled; the other was manually calibrated.
- ABC caused false daily baseline resets when CO2 did not fall to 400 ppm in a 24-hour period.
- ABC-related drops were corrected by comparing to the non-ABC sensor pattern.
- The non-ABC sensor was also found to undermeasure CO2 by about 450 ppm, so values were shifted upward by 450 ppm.
- Abnormal CO2 leakage was defined using a conservative 1000 ppm threshold, although Viefhues notes that around 800 ppm would already be suspicious in an unoccupied basement context.

### Features Used

For CO2 leakage analysis:

- CO2 leakage target
- PM10
- PM2.5
- Temperature
- Humidity
- Pressure
- Precipitation
- Period label
- Rhine water level
- Discharge
- Stream water level
- Groundwater level
- Mine-water level

For flood classification:

- Same broad variable set, with `IsFloodingPeriod` as the binary target.
- Feature-reduced variants use the most important variables from Random Forest feature importance.

### Target Variables

- `abnormal_Co2_leakage`: binary CO2 leakage indicator, based on CO2 > 1000 ppm.
- `IsFloodingPeriod`: binary flood-period indicator.
- `period`: categorical before/during/after flood label used for exploratory comparison and model splits.

### Models

- Random Forest classifiers.
- Hyperparameter optimization via random-search-style tuning.
- 10-fold cross-validation for model evaluation.
- ROC/AUC visualization, with ROC generated using 5-fold cross-validation.
- Random oversampling of the minority flood class to improve recall.

Reported Random Forest hyperparameters for flood models:

- `n_estimators`: 400
- `min_samples_split`: 5
- `min_samples_leaf`: 1
- `max_features`: `sqrt`
- `max_depth`: 30
- `bootstrap`: True

### Headline Results

CO2 and flood effect:

- CO2 leakage increased during the flood and remained elevated after the flood.
- Mean CO2:
  - Before: 1058.99 ppm
  - During: 1697.26 ppm
  - After: 1309.04 ppm
- Leakage-event share:
  - Before: 31.4%
  - During: 52.5%
  - After: 38.5%
- All periods reached sensor maximum CO2 values of 5000 ppm.
- Humidity was elevated during and after the flood.
- Discharge increased sharply during the flood; mean discharge during the flood was more than three times the pre-flood mean.
- Groundwater and mine-water levels increased prior to the flood, accelerated during it, and continued rising after it.

CO2 driver analysis:

- Before flood: pressure was the most influential CO2 leakage predictor, followed by humidity and Rhine water level.
- During flood: pressure became much more dominant than before.
- After flood: Rhine water level became the most important variable, followed by humidity and pressure.
- During the flood, CO2 had a strong negative correlation with pressure.
- After the flood, humidity and Rhine water showed stronger relationships with CO2, and mine/groundwater were moderately related.

Flood classification:

- All-variable Random Forest and eight-variable Random Forest both reached AUC about 0.98.
- Model 1, all variables: precision 0.90, recall 0.84, F1 0.79.
- Model 2, eight important variables: precision 0.90, recall 0.84, F1 0.78.
- Model 3, minority class oversampled to 6%: precision 0.90, recall 0.99, F1 0.91.
- Oversampling to 20% produced recall 1.00 and was treated as suspicious for overfitting.
- Model without ground- and mine-water: precision 0.91, recall 0.84, F1 0.79.
- Mine water was the most important flood-classification feature, followed by groundwater; Rhine and stream water also mattered.
- Precipitation and discharge were not identified as significant model drivers, but Viefhues explicitly warns that this contradicts hydrological expectation and likely reflects too few heavy-precipitation observations.

### Explicit Limitations

- Single case study at one house / one site.
- Single flood event; results have limited generalizability.
- Flood-period boundaries are uncertain and sensitive to threshold movement by a few days.
- Precipitation was likely underrepresented because there were only a few heavy-rain observations.
- Random Forest and oversampling create overfitting risk despite hyperparameter tuning and cross-validation.
- The 20% oversampling model likely overfit.
- ABC autocalibration correction is a methodological vulnerability; Viefhues recommends more resources for a more precise solution.
- ANN or other stronger models were not used due to limited resources.
- Larger datasets and additional flood events are needed.

### What This Chapter Inherits

- The Kerkrade site is a real CO2 leakage setting linked to closed mine infrastructure.
- July 2021 produced a measurable increase in CO2 leakage frequency and concentration.
- Pressure is a key CO2 confound/driver and must be decomposed before making hydrological claims.
- Groundwater and mine-water are central to the flood/hydrological interpretation.
- Water-level/discharge data are necessary, not optional.
- The 1000 ppm CO2 threshold is an established predecessor convention.
- Hourly alignment is an established predecessor convention.
- The ABC autocalibration issue must be checked again in the 2025-present data.
- The Jean Hacking / Rene Mols route is a plausible route for obtaining mine/groundwater data.

### What This Chapter Must Do Differently

- Do not treat the July 2021 event as the analyzed event if the current empirical window is Jan 2025-present; use 2021 as predecessor/motivation.
- Do not simply classify before/during/after one known flood. Build a soft event catalogue from discharge in the new window.
- Do not rely on random k-fold or ordinary cross-validation for time-series claims; use time-aware splits for chapter models.
- Do not let pressure dominate the story without explicit decomposition. First ask how much CO2 variance pressure level/tendency explains.
- Do not claim flood prediction unless labels and evaluation support it. The chapter is better framed as signal characterization and hydrological antecedent-state detection.
- Do not overstate generalization from a single calibration site. Any transfer test should be framed as a stress test, not universal portability.
- Revisit feature importance with modern, time-aware, leakage-aware methods; Random Forest impurity importance alone is not enough.
- Treat precipitation/discharge carefully: Viefhues' model underweighted them despite hydrological expectation, probably because of event sparsity.

## Eryilmaz 2025

### Citation / Identity

S. Eryilmaz. 2025. "Predicting CO2 leakages in post-industrial mining zones: the case of Limburg." Paper draft / article-style manuscript, 11 pages.

### Central Purpose

Eryilmaz asks whether basement CO2 leak events at the Kerkrade site can be predicted from environmental variables, and whether public weather-station data can substitute for on-site IoT variables with only a small loss of predictive performance.

The paper is narrower than Viefhues. It is not a flood paper and does not analyze July 2021. It is a same-site CO2 leakage prediction paper.

### Data Window

- September 13, 2020 to May 31, 2021.
- 2,453 hourly observations common to basement, living-room, and weather-station sources.
- This window excludes the July 2021 flood.

### Data Sources

IoT:

- Two indoor sensors in a Kerkrade residence above a closed mineshaft.
- Basement sensor = test unit.
- Living-room sensor = control.

Measured variables:

- Temperature
- Relative humidity
- Atmospheric pressure
- CO2
- Light
- PM2.5
- PM10

Weather:

- Publicly available meteorological data accessed through Visual Crossing.

### Data Preparation

- Sensor readings were recorded at one-minute intervals.
- Timestamps were standardized to UTC.
- Data were reindexed to hourly intervals.
- Missing values were filled using the nearest data point within a 20-minute window.
- Light, PM2.5, and PM10 were excluded from prediction because they had weak or insignificant correlations with CO2.
- Six-hour temporal change terms were computed, especially 6-hour air-pressure change.

### Features Used

Model A: indoor IoT feature model:

- Temperature
- Relative humidity
- Atmospheric pressure
- Six-hour change in atmospheric pressure

Model B: public-weather feature model:

- Weather-station temperature
- Weather-station relative humidity
- Weather-station atmospheric pressure
- Six-hour change in atmospheric pressure

The target remains the basement CO2 leak event in both models. Eryilmaz substitutes features; it does not remove CO2 as the target and does not predict transfer-site outcomes.

### Target Variable

- Binary CO2 leak event: basement CO2 > 1000 ppm.

### Models

- Logistic regression / generalized linear model.
- 5-fold cross-validation.
- AUROC used as the primary metric.

### Headline Results

Descriptive:

- Basement CO2 was much higher and more variable than living-room CO2.
- Basement CO2 summary: mean 742.7 ppm, SD 621.6, max 4431 ppm.
- Living-room CO2 summary: mean 533.0 ppm, SD 32.2, max 701 ppm.
- Indoor pressure series were nearly identical between basement and living room; the weather station had a higher mean pressure due to altitude/open-air context, but the changes followed the same pattern.
- Basement CO2 was most strongly related to atmospheric pressure and its temporal variation.

Prediction:

- Indoor IoT logistic model with 6-hour pressure change: AUROC 0.96.
- Without the 6-hour pressure-change term, predictive performance drops substantially; the extracted figure text indicates about 0.67.
- Public-weather logistic model: AUROC 0.94.
- Eryilmaz interprets the small AUROC difference as evidence that nearby public weather data can substitute for on-site environmental sensing for this same-site target.

### Explicit Limitations

- Single site / case-specific result.
- Other mining areas may have different leakage behavior due to local geology and environmental conditions.
- Broader applicability requires case-specific testing in additional locations.
- The paper is not a cross-site transfer study.
- The data window excludes the July 2021 flood, so the result applies to a normal-period window rather than flood-extreme conditions.
- The weather-station model still predicts a basement CO2 target from the calibration site; it does not remove the need for a target site during model development.

### What This Chapter Inherits

- The external-weather substitution premise: public weather variables can capture most of the predictive signal for basement CO2 leak events at the Kerkrade calibration site.
- Six-hour pressure change is a crucial feature and should be explicitly replicated.
- The 1000 ppm leak-event threshold and hourly alignment conventions are inherited.
- Visual Crossing is needed for faithful replication of Eryilmaz's setup.
- Eryilmaz's result is an important empirical reason to ask what the non-CO2 weather/environmental signal is actually carrying.

### What This Chapter Must Do Differently

- Replicate Eryilmaz faithfully first, using the same target definition and a comparable weather-feature model, before treating the result as a premise.
- Keep the random 5-fold setup confined to the replication exercise; chapter models should use time-aware evaluation.
- Do not describe Eryilmaz as proving transfer. It proves same-site feature substitution.
- Do not say Eryilmaz "removed CO2" as a feature in a transfer model. The CO2 target remains the same basement CO2 event.
- Extend from binary CO2 leak prediction to continuous signal characterization and anomaly detection.
- Test whether the signal structure has any useful relationship to hydrological soft labels, not merely whether weather predicts CO2 > 1000 ppm.
- If transfer sites lack CO2 targets, make the transfer experiment explicit as a stress test with local hydrological labels, not a direct repeat of Eryilmaz.

## Joint Implications for This Chapter

### What Is Established

- Kerkrade is a real calibration site above closed mine infrastructure with measurable basement CO2 leakage.
- CO2 leakage is related to pressure, and pressure must be treated as the first-order confound.
- The July 2021 flood increased CO2 leakage frequency and concentration at the site.
- Mine/groundwater dynamics matter for the hydrological interpretation.
- Weather-station variables, especially pressure tendency, can predict the same-site CO2 leakage target nearly as well as indoor environmental features in a non-flood window.

### What Is Not Established

- That the 2025-present window contains a comparable hydrological event.
- That residual CO2 signal remains after pressure level and tendency are decomposed.
- That the weather/IoT signal transfers beyond Kerkrade.
- That public weather alone can identify antecedent hydrological state at other Maas-basin sites.
- That Random Forest feature importance from one event can serve as a defensible causal explanation.

### Immediate PW-1 / June Follow-Through

- Re-check the IoT data for ABC autocalibration artifacts and baseline shifts.
- Keep hourly alignment as the first common resolution.
- Use Visual Crossing for the Eryilmaz replication, but pull KNMI as the reference met source for chapter inference.
- Build discharge-based soft labels for Worm/Wurm and Geul events in the 2025-present window.
- Replicate Eryilmaz's two logistic models on the new data window:
  - Model A: indoor temp, humidity, pressure, 6-hour pressure change.
  - Model B: outdoor weather temp, humidity, pressure, 6-hour pressure change.
- Record a decisions-log entry that random 5-fold CV is used only for faithful predecessor replication, not for the chapter's own time-series evaluation.
- Run the pressure-decomposition kill check before committing to the hydrological-signal claim.

### Framing Sentence for the Chapter

Viefhues establishes that the Kerkrade mine-gas signal responds to the July 2021 flood and that hydrological variables matter; Eryilmaz establishes that public weather features can substitute for indoor environmental features in predicting same-site CO2 leak events during a non-flood window. This chapter takes those findings as calibration-site premises and asks the next question: after pressure effects are explicitly separated, does the remaining multivariate signal contain usable antecedent-hydrological-state information, and does any part of that signal survive a transfer stress test beyond Kerkrade?
