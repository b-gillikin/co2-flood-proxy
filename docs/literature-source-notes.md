# Literature Source Notes

These notes describe individual sources. They do not provide a cross-source
synthesis, a chapter argument, a novelty claim or a proposed interpretation of
future results. Author-reported findings and limitations remain attributed to
the source. The evidence-question IDs connect each entry to
`literature-evidence-matrix.csv`.

## Evidence questions

- **Q01:** What did Viefhues report about indoor CO2 around the July 2021 event?
- **Q02:** How did Viefhues define, process and model CO2 and the flood period?
- **Q03:** What did Eryilmaz test outside the flood period, with what scope?
- **Q04:** How can atmospheric pressure influence subsurface or mine-gas emission?
- **Q05:** What mine-water and mine-gas conditions are documented for Aachen and South Limburg?
- **Q06:** What rainfall and runoff characteristics were reported for July 2021 in Limburg and nearby basins?
- **Q07:** What measurement and reconstruction uncertainties affect the July 2021 record?
- **Q08:** How are recent rainfall totals related to flood response?
- **Q09:** How do antecedent wetness, snow or baseflow condition flood response?
- **Q10:** How do flood-generating mechanisms vary by region and season?
- **Q11:** What temporal windows and conditioning variables are used in flood-event studies?
- **Q12:** How is spatial synchrony of high flows defined and measured?
- **Q13:** How is the dependence between high flows related to distance?
- **Q14:** How do storm, catchment and land-surface properties affect flood spatial extent?
- **Q15:** How are regional flood events and their spatial footprints constructed?
- **Q16:** What is gained and assumed when using peaks over threshold rather than annual maxima?
- **Q17:** How can threshold exceedances be declustered into approximately independent episodes?
- **Q18:** How can episodes at different gauges be grouped into regional storms?
- **Q19:** How sensitive are event samples and estimates to thresholds and measurement uncertainty?
- **Q20:** What are the relevant characteristics and limitations of RADOLAN/RADKLIM rainfall products?
- **Q21:** How do rating curves, gauge failure and censoring affect high-flow observations?
- **Q22:** Which atmospheric variables accompany extreme rainfall and flash-flood occurrence?
- **Q23:** What long-record public-weather products can supply hourly temperature, humidity and pressure, and what are their measurement limitations?
- **Q24:** How does current operational-AI work in Limburg distinguish experimental flood information from an authorized warning system?

## Predecessors and the Kerkrade mechanism

### Viefhues2022 — Viefhues (2022)

- **Citation:** Jan-Philipp Viefhues. *Prediction of CO2 Leakage and Flood Using Machine Learning Models: A Data Driven Approach in the Historic Coal Mining District in the Province of Limburg (Kerkrade).* Master's thesis, Maastricht University School of Business and Economics, 2022.
- **Official record:** Supplied thesis PDF, `chapter-prework/Jan_Philip_IDnr6258161_TIP%20Master%20Thesis.pdf`.
- **Type/status:** Completed master's thesis; not peer reviewed.
- **Objective and setting:** The thesis asks whether indoor IoT measurements in a Kerkrade building above former coal workings can describe CO2 leakage and the July 2021 flood period. It uses two indoor sensors, local IoT variables, weather, groundwater and mine-water information. The principal record runs from 25 August 2020 to 1 September 2021 and is aggregated from minute to hourly resolution.
- **Outcome and method:** CO2 above 1,000 ppm is treated as leakage. Flood-period labels are imposed around July 2021. Random-forest regressions and classifiers are fitted after cleaning, alignment and resampling. Atmospheric pressure is included as an explanatory variable.
- **Author-reported findings:** Mean CO2 was reported as 1,058.99 ppm before, 1,697.26 during and 1,309.04 after the flood period; the corresponding shares above 1,000 ppm were 31.4%, 52.5% and 38.5%. Pressure was the most important model input. The author presents the result as a single-site proof of concept rather than a validated flood signal.
- **Author-stated limitations and source discrepancies:** Only one flood is observed; heavy-rain examples are scarce; oversampling and model fit may overstate performance; the exact flood-period boundary is uncertain; and automatic baseline correction complicates interpretation. The thesis calls both sensors basement devices, while the supplied K3 filename says `livingroom`. The supplied code identifies K4 as non-ABC, but device identity, calibration, the precise ABC edits and the stated 450-ppm adjustment remain unresolved.
- **Locators/questions:** Abstract; §§4.2.2–4.2.5 and 5.1–5.4; Table 1; Figs. 3, 7–9 and 11. Q01, Q02, Q04.

### Eryilmaz2025 — Eryilmaz (2025)

- **Citation:** S. Eryilmaz. *Predicting CO2 Leakages in Post-Industrial Mining Zones: The Case of Limburg.* Unpublished manuscript, 2025.
- **Official record:** Supplied manuscript PDF, `chapter-prework/Eryilmaz-2025.pdf`.
- **Type/status:** Unpublished manuscript. The file name and citation year are 2025; the supplied PDF metadata records generation on 20 January 2026.
- **Objective and setting:** The manuscript tests whether public weather data can reproduce information supplied by indoor IoT measurements when classifying elevated CO2 in the same Kerkrade building studied by Viefhues. It distinguishes a basement test sensor from a living-room control sensor and covers 13 September 2020 through 31 May 2021, before the July flood.
- **Outcome and method:** The binary outcome is basement CO2 above 1,000 ppm. The common hourly analysis sample contains 2,453 observations. Logistic regressions compare public Visual Crossing weather variables with IoT variables; a six-hour pressure change is constructed and evaluated alongside pressure level and other weather measures.
- **Author-reported findings:** The public-weather specification with six-hour pressure change reaches an AUROC reported near 0.94, compared with about 0.65 without that change; the indoor-IoT specification is reported near 0.96. The manuscript highlights the small same-site performance difference and the importance of pressure dynamics.
- **Author-stated limitations:** The study uses one building and one historical period, does not test July 2021 or a high-water outcome, and calls for testing at additional sites. Its target remains an indoor threshold whose occupancy and sensor-processing context are not fully resolved in the supplied predecessor materials.
- **Locators/questions:** Abstract; §2; Tables 1–2; Figs. 3–7; §4. Q03, Q04.

### MeinersEtAl2016 — Meiners et al. (2016)

- **Citation:** Heribert Meiners, Michael Opahle, Gerhard Hölscher and Erwin Kunz. *Na-ijlende Gevolgen Steenkolenwinning Zuid-Limburg: Final Report on the Results of Working Group 5.2.6—Risk from Mine Gas.* DMT, 2016.
- **Official record:** <https://www.tweedekamer.nl/downloads/document?id=2016D49358>
- **Type/status:** Government-commissioned technical report submitted with the Dutch ministerial package on the after-effects of coal mining.
- **Objective and setting:** The working group assesses mine-gas hazards after mine closure in South Limburg. Its evidence concerns the Dutch mining district, mine shafts and workings, possible migration pathways, building exposure, pressure conditions and the consequences of mine-water rebound.
- **Outcome and method:** The report uses mining records, geological and hydrogeological information, gas composition and pressure evidence, documented incidents and structured risk assessment. The outcome is not river high water; it is the occurrence and potential consequence of mine-gas migration and accumulation.
- **Author-reported findings:** The report identifies carbon dioxide and methane as relevant post-mining gases, distinguishes source, pathway and receptor conditions, and treats barometric pressure and changing mine-water conditions as factors that can alter gas movement. It supports site-specific inspection and risk management because shafts, near-surface workings, sealing and building conditions vary.
- **Author-stated limitations:** Historical mine records and the physical condition of individual pathways are incomplete. The report does not provide an hourly Kerkrade sensor series, a flood-event test or a general quantitative mapping from rainfall to indoor CO2.
- **Locators/questions:** Executive summary; chapters on mine-gas generation, migration pathways, risk scenarios and proposed measures; Dutch parliamentary attachment 5.2.6. Q04, Q05.

### Rosner2011 — Rosner (2011)

- **Citation:** Peter Rosner. *Der Grubenwasseranstieg im Aachener und Südlimburger Steinkohlenrevier: Eine hydrogeologisch-bergbauliche Analyse der Wirkungszusammenhänge.* Doctoral dissertation, RWTH Aachen University, 2011.
- **Official record:** <https://publications.rwth-aachen.de/record/64267>
- **Type/status:** Doctoral dissertation with an institutional full-text record.
- **Objective and setting:** Rosner documents mine-water recovery after drainage ceased in 1993–1994 across roughly 490 km² of the transboundary Aachen–South Limburg coal district. The study describes more than 800 years of mining and the connected mine voids, Carboniferous bedrock and Cretaceous/Tertiary cover.
- **Outcome and method:** Mining records, water-level and water-chemistry observations, geological structure and hydraulic connections are assembled into an analogue conceptual model. Outcomes include the pace of mine-water rise, mine-water chemistry, mine-gas migration, ground movement and changes in groundwater head and quality.
- **Author-reported findings:** Rosner reports that recovery is governed jointly by mine connectivity and natural and mining-altered hydrogeological structures. The dissertation documents interactions between mine workings and cover strata and describes consequences for gas release, uplift and groundwater systems. It states that these process relationships may inform assessment in other coal districts.
- **Author-stated limitations:** The work emphasizes the complexity and changing nature of hydraulic connections and boundary conditions. It is a district-scale reconstruction, not a controlled estimate of the effect of a particular rainfall or river event on a particular building.
- **Locators/questions:** Institutional abstract; dissertation summaries; chapters on geological-mining structure, mine-water recovery, gas migration and monitoring. Q05.

### HeitfeldEtAl2002 — Heitfeld et al. (2002)

- **Citation:** K.-H. Heitfeld, M. Heitfeld, P. Rosner, H. Sahl and K. Schetelig. “Mine Water Recovery in the Coal Mining District of Aachen—Impacts and Measures to Control Potential Risks.” In *Uranium in the Aquatic Environment*, 1011–1020. Springer, 2002. DOI: <https://doi.org/10.1007/978-3-642-55668-5_119>.
- **Type/status:** Peer-reviewed conference-book chapter.
- **Objective and setting:** The chapter describes expected effects of mine-water recovery following closure and the end of dewatering in the Aachen coal district and connected South Limburg workings. It considers a mining area of approximately 400 km² and the cross-border hydraulic setting.
- **Outcome and method:** The authors compile mine plans, hydrogeological structure, observed and projected water levels and identified pathways. They evaluate potential effects on aquifers, receiving waters, mine-gas displacement and ground movement and discuss measures for controlling risk.
- **Author-reported findings:** The chapter describes recovery as a staged, spatially connected process rather than a local water-table response. Hydraulic connections between collieries and interactions with overlying strata determine the timing and location of effects. Monitoring and controlled pumping are discussed as ways to constrain uncertain future conditions.
- **Author-stated limitations:** Predictions depend on incomplete mine geometry and hydraulic-property information, and the authors frame monitoring as necessary because the system evolves during recovery. The chapter predates both the Kerkrade IoT record and the July 2021 flood and does not estimate event-scale indoor-gas responses.
- **Locators/questions:** Abstract; sections on hydrogeological setting, predicted recovery effects and control measures; pp. 1011–1020. Q05.

### CaroCuencaEtAl2013 — Caro Cuenca et al. (2013)

- **Citation:** Miguel Caro Cuenca, Andrew J. Hooper and Ramon F. Hanssen. “Surface Deformation Induced by Water Influx in the Abandoned Coal Mines in Limburg, The Netherlands Observed by Satellite Radar Interferometry.” *Journal of Applied Geophysics* 88 (2013): 1–11. DOI: <https://doi.org/10.1016/j.jappgeo.2012.10.003>.
- **Type/status:** Peer-reviewed research article.
- **Objective and setting:** The study investigates surface movement over abandoned coal mines in Limburg after mine-water influx. It treats the former mining district as a spatially heterogeneous subsurface system and asks whether satellite radar can identify deformation associated with changing underground water conditions.
- **Outcome and method:** Persistent-scatterer interferometry is applied to satellite synthetic-aperture-radar observations. Surface displacement patterns are compared with the location of former mining infrastructure and available information about mine-water recovery.
- **Author-reported findings:** The authors report spatially varying uplift associated with water influx and show that deformation does not follow a simple uniform surface. The observed pattern is interpreted through mine layout, hydraulic compartments and geological structure. The article supplies independent evidence that post-mining water changes can produce measurable surface effects in Limburg.
- **Author-stated limitations:** Attribution is constrained by the spatial and temporal coverage of radar observations and by incomplete knowledge of underground connections and water levels. The measured outcome is ground deformation, not gas flux, indoor CO2 or river high water. The paper therefore does not identify an hourly meteorological response or an event precursor.
- **Locators/questions:** Abstract; data and interferometric-method sections; deformation maps and discussion of mine-water recovery; Figs. 3–8. Q05.

### WronaEtAl2016 — Wrona et al. (2016)

- **Citation:** Paweł Wrona, Zenon Różański, Grzegorz Pach, Tomasz Suponik and Marcin Popczyk. “Closed Coal Mine Shaft as a Source of Carbon Dioxide Emissions.” *Environmental Earth Sciences* 75 (2016): 1139. DOI: <https://doi.org/10.1007/s12665-016-5977-7>.
- **Type/status:** Peer-reviewed research article.
- **Objective and setting:** The authors examine carbon-dioxide release from a closed hard-coal mine shaft in Poland. The setting is an engineered post-mining pathway open to atmospheric forcing rather than an occupied Limburg building.
- **Outcome and method:** Field instruments record gas composition and emission conditions at the shaft while meteorological variables are monitored. The analysis relates observed CO2 release to atmospheric and shaft conditions and considers the safety implications of dense CO2 accumulating near ground level.
- **Author-reported findings:** The paper documents episodic CO2 emission from the closed shaft and reports relationships between emissions and meteorological conditions, especially atmospheric pressure. The authors describe the shaft as a pathway capable of linking underground gas reservoirs to the surface and identify periods when emissions may create a local hazard.
- **Author-stated limitations:** Measurements concern one shaft and its construction, underground connectivity and local weather. The authors do not claim that the estimated relationships transfer directly to buildings or other mines. The study does not involve river flooding, catchment rainfall or mine-water observations sufficient to separate pressure forcing from hydrological forcing.
- **Locators/questions:** Abstract; site and monitoring description; time-series figures; discussion of pressure and emission episodes; conclusions. Q04.

### WronaEtAl2025 — Wrona et al. (2025)

- **Citation:** Paweł Wrona, Zenon Różański, Grzegorz Pach, Adam P. Niewiadomski, Małgorzata Markowska, Aleksander Król, Małgorzata Król and Andrzej Chmiela. “Selected Meteorological Factors Influencing Gas Emissions from an Abandoned Coal Mine Shaft—Results of In Situ Measurements.” *Sustainability* 17 (2025): 3875. DOI: <https://doi.org/10.3390/su17093875>.
- **Type/status:** Peer-reviewed research article.
- **Objective and setting:** This study revisits meteorological control of gas movement at an abandoned coal-mine shaft in Poland using in-situ measurements. It asks how atmospheric pressure, temperature and related changes correspond with exchange between the mine atmosphere and the surface.
- **Outcome and method:** Hourly meteorological and shaft-gas observations are compared in time, including changes rather than pressure level alone. The analysis considers lags and the inertia of the subsurface response during changing atmospheric conditions.
- **Author-reported findings:** The authors report that falling atmospheric pressure promotes outward gas movement and that the shaft response can persist into the early part of a pressure rise. Temperature differences also influence exchange. The observed response is dynamic, so a single contemporaneous pressure value does not fully describe the episode.
- **Author-stated limitations:** Results depend on the monitored shaft, its connection to workings and local meteorology. The study does not measure indoor occupancy, building ventilation, river high water or the Limburg mine-water system. Its lag patterns are therefore source-specific observations, not fixed adjustment coefficients for Kerkrade.
- **Locators/questions:** Abstract; monitoring and variable definitions; pressure-change and temperature analyses; result figures; discussion and conclusions. Q04, Q11.

### FordeEtAl2019 — Forde et al. (2019)

- **Citation:** Olenka N. Forde, Aaron G. Cahill, Roger D. Beckie and K. Ulrich Mayer. “Barometric-Pumping Controls Fugitive Gas Emissions from a Vadose Zone Natural Gas Release.” *Scientific Reports* 9 (2019): 14080. DOI: <https://doi.org/10.1038/s41598-019-50426-3>.
- **Type/status:** Peer-reviewed controlled field experiment.
- **Objective and setting:** The authors test how weather controls surface expression of a shallow subsurface gas release. Natural gas was injected approximately 12 m below ground for five days at a site with a roughly 60 m unsaturated zone; monitoring continued for 24 days.
- **Outcome and method:** Gas concentration and flux were measured in the subsurface and at the ground surface alongside barometric pressure, precipitation and temperature. The controlled injection gives known release timing, while natural meteorological variability provides the forcing contrast.
- **Author-reported findings:** Declining barometric pressure produced rapid surface breakthrough and changes exceeding twenty-fold within less than a day. Pressure variation dominated precipitation and temperature in explaining the short-term surface signal. The study describes this as barometric pumping of stored gas through the vadose zone.
- **Author-stated limitations:** The authors emphasize that geological layering, permeability, water content and release geometry affect migration and surface detection. The injected gas, unsaturated formation and open ground surface differ from an abandoned mine and an occupied basement. The experiment establishes a plausible pressure mechanism but does not estimate a flood-related indoor CO2 response.
- **Locators/questions:** Abstract; field-site and injection design; monitoring results; discussion of meteorological controls; main time-series and flux figures. Q04, Q11.

## Limburg and the July 2021 high-water event

### TsiokanosEtAl2024 — Tsiokanos et al. (2024)

- **Citation:** Athanasios Tsiokanos, Martine Rutten, Ruud J. van der Ent and Remko Uijlenhoet. “Flood Drivers and Trends: A Case Study of the Geul River Catchment (the Netherlands) over the Past Half Century.” *Hydrology and Earth System Sciences* 28 (2024): 3327–3345. DOI: <https://doi.org/10.5194/hess-28-3327-2024>.
- **Type/status:** Peer-reviewed research article.
- **Objective and setting:** The paper investigates flood-generating conditions and trends in the Geul, a fast-responding transboundary tributary in South Limburg. It uses the Meerssen discharge record from 1970 through August 2021 together with precipitation, soil-moisture and climatic information.
- **Outcome and method:** Fifteen-minute discharge is used to identify high-flow events and examine their seasonality, trends and associations with rainfall and antecedent state. July 2021 is analysed within the long record. The authors compare precipitation totals and catchment wetness for historical peaks rather than treating short rainfall intensity as a sufficient event definition.
- **Author-reported findings:** Extreme 24-hour rainfall did not invariably generate an extreme discharge. Prolonged precipitation and wet initial conditions were important for large responses. The Geul typically responds over about one to two days. For July 2021, the observed discharge near Meerssen reached roughly 55 m³/s, while reconstruction suggested a peak above 80 m³/s because the measurement did not capture the full event.
- **Author-stated limitations:** The discharge series includes measurement and rating-curve uncertainty, especially during July 2021; soil-moisture products do not directly observe every relevant storage; and a single catchment limits geographic interpretation.
- **Locators/questions:** Abstract; §§2.2–2.4 and 3.1–3.4; event and trend figures; July 2021 discussion; conclusions. Q06, Q08, Q09, Q21.

### MohrEtAl2023 — Mohr et al. (2023)

- **Citation:** Susanna Mohr, Uwe Ehret, Michael Kunz, Patrick Ludwig, Alberto Caldas-Alvarez, James E. Daniell, Florian Ehmele, Hendrik Feldmann, Mário J. Franca, Christian Gattke, Marie Hundhausen, Peter Knippertz, Katharina Küpfer, Bernhard Mühr, Joaquim G. Pinto, Julian Quinting, Andreas M. Schäfer, Marc Scheibel, Frank Seidel and Christina Wisotzky. “A Multi-Disciplinary Analysis of the Exceptional Flood Event of July 2021 in Central Europe—Part 1: Event Description and Analysis.” *Natural Hazards and Earth System Sciences* 23 (2023): 525–551. DOI: <https://doi.org/10.5194/nhess-23-525-2023>.
- **Type/status:** Peer-reviewed multidisciplinary event study.
- **Objective and setting:** The article reconstructs the meteorological, hydrological and impact sequence of the 12–19 July 2021 event across western Germany and neighbouring areas. Detailed analyses include the Ahr, Erft and other severely affected catchments within the broader central-European storm.
- **Outcome and method:** Weather-station, radar, reanalysis, river-gauge, field-survey and impact records are combined. Damaged or exceeded gauges are supplemented by hydraulic reconstruction and post-event evidence. The study distinguishes observed values from estimates and discusses uncertainty in reconstructed peak flow.
- **Author-reported findings:** The storm produced locally around 150 mm of rain within approximately 15–18 hours, following antecedent rainfall. Rapid runoff in steep and partly saturated catchments caused extraordinary peaks, inundation and geomorphic change. Gauge destruction, altered cross sections, backwater and rating-curve extrapolation complicated peak estimation. Reported reconstruction uncertainty for some flows is on the order of 15–20%, and the authors state that estimates can be revised as evidence improves.
- **Author-stated limitations:** Rainfall products differ in complex terrain, several discharge gauges failed or were outside calibrated ranges, and impact evidence is incomplete. The article cautions against treating reconstructed peaks as direct observations.
- **Locators/questions:** Abstract; §§2–4; meteorological and hydrological chronologies; Tables 2–4; Figs. 3–13; uncertainty discussion. Q06, Q07, Q21.

### LudwigEtAl2023 — Ludwig et al. (2023)

- **Citation:** Patrick Ludwig, Florian Ehmele, Mário J. Franca, Susanna Mohr, Alberto Caldas-Alvarez, James E. Daniell, Uwe Ehret, Hendrik Feldmann, Marie Hundhausen, Peter Knippertz, Katharina Küpfer, Michael Kunz, Bernhard Mühr, Joaquim G. Pinto, Julian Quinting, Andreas M. Schäfer, Frank Seidel and Christina Wisotzky. “A Multi-Disciplinary Analysis of the Exceptional Flood Event of July 2021 in Central Europe—Part 2: Historical Context and Relation to Climate Change.” *Natural Hazards and Earth System Sciences* 23 (2023): 1287–1311. DOI: <https://doi.org/10.5194/nhess-23-1287-2023>.
- **Type/status:** Peer-reviewed historical and modelling event study.
- **Objective and setting:** Part 2 places the July 2021 event in a historical record and examines how warmer thermodynamic conditions could alter similar rainfall and runoff. It focuses on affected western-European catchments and uses reconstructed high flows at ten gauges.
- **Outcome and method:** Historical documentary and instrumental evidence is combined with atmospheric pseudo-global-warming experiments and hydrological simulations. The authors perturb temperature conditions while retaining the event’s circulation pattern and propagate simulated rainfall through catchment models.
- **Author-reported findings:** July 2021 is reported as exceptional in both meteorological and hydrological terms but not without historical analogues. In one approximately +2 K experiment, basin-average rainfall increased by about 18%, while the simulated Ahr peak rose by about 39%, illustrating nonlinear rainfall–runoff response. The magnitude differs by catchment and scenario.
- **Author-stated limitations:** Several observed peaks require reconstruction, historical documentary series are incomplete, and the pseudo-global-warming method does not sample changes in event frequency or circulation. Hydrological results depend on model structure, initial state and uncertain high-flow calibration. The results concern a specific event storyline rather than a forecast model or an observed transfer radius.
- **Locators/questions:** Abstract; historical comparison; atmospheric methods; hydrological modelling; Figs. 4–12; discussion and conclusions. Q06, Q07, Q10.

### TradowskyEtAl2023 — Tradowsky et al. (2023)

- **Citation:** Jordis S. Tradowsky, Sjoukje Y. Philip, Frank Kreienkamp, Sarah F. Kew, Philip Lorenz, Julie Arrighi, Thomas Bettmann, Steven Caluwaerts, Steven C. Chan, Lesley De Cruz, Hylke de Vries, Norbert Demuth, Andrew Ferrone, Erich M. Fischer, Hayley J. Fowler, Klaus Goergen, Dorothy Heinrich, Yvonne Henrichs, Frank Kaspar, Geert Lenderink, Enno Nilson, Friederike E. L. Otto, Francesco Ragone, Sonia I. Seneviratne, Roop K. Singh, Amalie Skålevåg, Piet Termonia, Lisa Thalheimer, Maarten van Aalst, Joris Van den Bergh, Hans Van de Vyver, Stéphane Vannitsem, Geert Jan van Oldenborgh, Bert Van Schaeybroeck, Robert Vautard, Demi Vonk and Niko Wanders. “Attribution of the Heavy Rainfall Events Leading to Severe Flooding in Western Europe during July 2021.” *Climatic Change* 176 (2023): 90. DOI: <https://doi.org/10.1007/s10584-023-03502-7>.
- **Type/status:** Peer-reviewed climate-event attribution study.
- **Objective and setting:** The study estimates how human-caused climate change affected the likelihood and intensity of the one- and two-day rainfall that produced July 2021 flooding. The analysis defines two western-European regions: the Ahr–Erft area and a larger region including parts of the Meuse basin.
- **Outcome and method:** Observational records and multiple climate-model ensembles are used in an event-attribution framework. Extreme rainfall is represented with annual maxima over moving spatial windows, and present-day conditions are compared with a cooler counterfactual climate. The hydrological consequences are described but are not the fitted outcome.
- **Author-reported findings:** The authors report that the heavy rainfall was rare in any individual location and that warming increased both its likelihood and intensity. They present ranges reflecting observational and model uncertainty rather than a single deterministic attribution number. Antecedent soil saturation is described as contributing to the flooding but is outside the rainfall-attribution estimand.
- **Author-stated limitations:** The event is rare relative to available records, spatial dependence limits the effective sample, model ensembles differ, and the analysis attributes rainfall rather than river discharge or damage. Results apply to the defined regions and event metric, not to individual Limburg tributary onset times.
- **Locators/questions:** Abstract; event and region definition; observational and model methods; synthesis of attribution results; uncertainty and discussion sections. Q06, Q22.

### AsselmanVanHeeringen2023 — Asselman and van Heeringen (2023)

- **Citation:** Nathalie E. M. Asselman and Kees J. van Heeringen. *Een watersysteemanalyse—wat leren we van het hoogwater van juli 2021? Inzichten in het functioneren van beeksystemen bij grote hoeveelheden neerslag en het effect van verschillende typen maatregelen.* Deltares project 11207700, 2023.
- **Official record:** <https://kennisbank.deltares.nl/pub/Details/fullCatalogue/300078862>
- **Type/status:** Technical report commissioned by Waterschap Limburg.
- **Objective and setting:** The report analyses the regional water system during July 2021 and evaluates the functioning of South Limburg streams, slopes, soils, sewers and retention measures. It addresses the Geul, Geleenbeek, Roer and other regional systems at a level relevant to local water management.
- **Outcome and method:** Observed rainfall and flow information, hydrological and hydraulic models, inundation evidence and scenario calculations are combined. The authors estimate water balances and test packages of structural and spatial measures under an event of July 2021 magnitude.
- **Author-reported findings:** The report characterizes the rainfall as an approximately two-day extreme with a very long return period. It estimates that roughly 30% of event rainfall was discharged through streams while the remainder was temporarily stored, infiltrated or otherwise retained in the system. Modelled measures can reduce local water levels and damages but do not eliminate flooding under this event.
- **Author-stated limitations:** Rainfall fields, runoff generation, hydraulic representation and undocumented local obstructions introduce uncertainty. Scenarios depend on model assumptions and are not observations of measure performance. The report is a system analysis, not a study of pre-event signal recurrence or indoor CO2.
- **Locators/questions:** Executive summary; chapters on rainfall, system functioning and water balance; model and measure scenarios; conclusions. Q06, Q08, Q09.

### SaadiEtAl2023 — Saadi et al. (2023)

- **Citation:** Mohamed Saadi, Carina Furusho-Percot, Alexandre Belleflamme, Ju-Yu Chen, Silke Trömel and Stefan Kollet. “How Uncertain Are Precipitation and Peak Flow Estimates for the July 2021 Flooding Event?” *Natural Hazards and Earth System Sciences* 23 (2023): 159–177. DOI: <https://doi.org/10.5194/nhess-23-159-2023>.
- **Type/status:** Peer-reviewed uncertainty study.
- **Objective and setting:** The authors assess how quantitative-precipitation-estimate choice and hydrological-model choice affect reconstructed July 2021 rainfall and peak discharge in seven western-German catchments.
- **Outcome and method:** Seven radar-based precipitation products drive two contrasting hydrological models, GR4H and ParFlow-CLM. Simulated peaks and hydrographs are compared across rainfall products and parameter sets. The exercise is an ensemble sensitivity analysis because observed event peaks are unavailable at the study outlets.
- **Author-reported findings:** Radar products without adequate vertical-profile correction tended to underestimate heavy precipitation. Differences among precipitation estimates were catchment dependent. Parameter uncertainty could exceed the spread attributable to rainfall products, and combinations that reproduced ordinary flow did not necessarily agree during the extreme. The paper reports a wide range of plausible event peaks rather than selecting one exact reconstruction.
- **Author-stated limitations:** There are no reliable observed peak flows for validating the event simulations; all studied catchments are regulated to some degree; radar correction remains uncertain; and each model represents processes differently. The authors caution that agreement among simulations is not direct evidence of accuracy.
- **Locators/questions:** Abstract; §§2.1–2.5; precipitation-product comparison; Figs. 3–10; discussion of uncertainty; conclusions. Q07, Q20, Q21.

### RongenEtAl2024 — Rongen et al. (2024)

- **Citation:** Guus Rongen, Oswaldo Morales-Nápoles and Matthijs Kok. “Using the Classical Model for Structured Expert Judgment to Estimate Extremes: A Case Study of Discharges in the Meuse River.” *Hydrology and Earth System Sciences* 28 (2024): 2831–2848. DOI: <https://doi.org/10.5194/hess-28-2831-2024>.
- **Type/status:** Peer-reviewed methodological case study.
- **Objective and setting:** The paper evaluates whether structured expert judgement can supplement statistical estimates of extreme Meuse discharges, including tributary contributions and spatial dependence that are poorly represented in short observational records.
- **Outcome and method:** Seven experts provide calibrated quantile judgements using the Classical Model. Their distributions are combined with generalized-extreme-value fits and elicited correlations for Meuse locations. The authors compare measurement-based, expert-only and combined descriptions of rare discharge.
- **Author-reported findings:** Gauge observations are more informative for frequently observed flows, while expert assessments add information in the far tail and for dependence. The combined results are presented as plausible distributions rather than observed event values. Experts identify rating-curve extrapolation and spatial correlation as central sources of uncertainty. The paper notes that the July 2021 combination was absent from a large synthetic summer ensemble used in Dutch flood-risk work.
- **Author-stated limitations:** Expert results depend on elicitation design and calibration questions, and extreme correlations are difficult to validate. Rating curves are incomplete at exceptional levels. The method supplies uncertainty distributions for risk analysis; it does not estimate event-minus-quiet signal decay with donor distance.
- **Locators/questions:** Abstract; §§2–4; elicitation and combination equations; Tables 1–5; discussion of measurements, experts and dependence. Q07, Q12, Q21.

## Rainfall, antecedent state and flood-generating processes

### MerzBloeschl2003 — Merz and Blöschl (2003)

- **Citation:** Ralf Merz and Günter Blöschl. “A Process Typology of Regional Floods.” *Water Resources Research* 39 (2003): 1340. DOI: <https://doi.org/10.1029/2002WR001952>.
- **Type/status:** Peer-reviewed canonical process-classification study.
- **Objective and setting:** The paper develops a process-based classification of flood events for Austrian catchments. It asks whether regional information on event-generating mechanisms can improve interpretation beyond a classification based on flood magnitude alone.
- **Outcome and method:** Annual maximum floods from 1971–1997 are assigned to five process types: long-rain floods, short-rain floods, flash floods, rain-on-snow floods and snowmelt floods. Classification uses event weather, snow and catchment information, including expert hydrological interpretation. The authors map process prevalence and compare process-specific seasonality and regional patterns.
- **Author-reported findings:** Different mechanisms dominate different Austrian regions and seasons. Long-rain floods are widespread in larger northern catchments, while flash floods and other types have distinct spatial and seasonal signatures. The process label provides information not contained in peak magnitude alone and helps explain regional differences in flood frequency behaviour.
- **Author-stated limitations:** Classification requires judgement and depends on the available meteorological and snow information. Some events contain mixed mechanisms, so discrete types simplify a continuum. The Austrian annual-maximum sample does not directly specify a Limburg threshold, precursor window or distance-decay estimator.
- **Locators/questions:** Abstract; §§2–4; process-definition table; maps of process occurrence and seasonality; discussion and conclusions. Q10, Q14.

### BerghuijsEtAl2016 — Berghuijs et al. (2016)

- **Citation:** Wouter R. Berghuijs, Ross A. Woods, Christopher J. Hutton and Murugesu Sivapalan. “Dominant Flood Generating Mechanisms across the United States.” *Geophysical Research Letters* 43 (2016): 4382–4390. DOI: <https://doi.org/10.1002/2016GL068070>.
- **Type/status:** Peer-reviewed large-sample hydrology study.
- **Objective and setting:** The authors identify the dominant generating mechanisms of annual floods across 420 minimally disturbed U.S. catchments with at least 20 years of data. The study asks how climate and catchment water balance organize the geography and seasonality of flood processes.
- **Outcome and method:** Annual maximum discharge events are linked to candidate rainfall, excess-rainfall, snowmelt and rain-on-snow mechanisms. Daily meteorological and hydrological data are used to compare the seasonal timing of candidate drivers with observed floods and to assign dominant mechanisms by catchment.
- **Author-reported findings:** Flood seasonality and dominant mechanism differ substantially across the United States. Excess rainfall, short- and long-duration precipitation, snowmelt and rain-on-snow each dominate in different hydroclimatic regimes. Antecedent storage conditions affect whether a given precipitation input becomes an annual flood.
- **Author-stated limitations:** Daily data cannot resolve sub-daily flash-flood mechanisms, process labels simplify mixed events, and the attribution rests on available gridded meteorology and conceptual indicators. Results from U.S. catchments are not parameter estimates for South Limburg and do not define spatial transfer between nearby gauges.
- **Locators/questions:** Abstract; data and mechanism definitions; national maps; seasonal analyses; supporting-information sensitivity checks. Q09, Q10.

### TarasovaEtAl2020 — Tarasova et al. (2020)

- **Citation:** Larisa Tarasova, Stefano Basso, Dörte Wendi, Alberto Viglione, Rohini Kumar and Ralf Merz. “A Process-Based Framework to Characterize and Classify Runoff Events: The Event Typology of Germany.” *Water Resources Research* 56 (2020): e2019WR026951. DOI: <https://doi.org/10.1029/2019WR026951>.
- **Type/status:** Peer-reviewed large-sample event study.
- **Objective and setting:** The article constructs a data-driven but process-informed typology of runoff events in 392 German catchments. It seeks a consistent description of event precipitation, antecedent storage and runoff response across regions.
- **Outcome and method:** Approximately 180,000 runoff events are separated from continuous records. Events are represented by dimensionless precipitation space-time characteristics and indicators of antecedent snow, frozen soil and soil moisture. Clustering and classification identify event types and six regional hydroclimatic groupings; uncertainty and sensitivity analyses examine the robustness of assignments.
- **Author-reported findings:** Event types and their prevalence vary across Germany and across seasons. Similar runoff magnitudes can arise from different combinations of precipitation structure and antecedent conditions. The authors report that incorporating both event forcing and catchment state provides a more informative event description than rainfall depth alone.
- **Author-stated limitations:** Event separation, gridded inputs and inferred soil or snow states introduce uncertainty. Cluster solutions impose discrete labels on overlapping process combinations, and uncertainty increases for sparsely observed extremes. The framework is designed for event characterization; it does not prescribe a 72-hour precursor contrast or a donor-distance function.
- **Locators/questions:** Abstract; §§2.2–2.5; event-characteristic definitions; §§3–4; type maps and uncertainty analysis. Q10, Q15, Q17.

### BrunnerDougherty2022 — Brunner and Dougherty (2022)

- **Citation:** Manuela I. Brunner and Erin M. Dougherty. “Varying Importance of Storm Types and Antecedent Conditions for Local and Regional Floods.” *Water Resources Research* 58 (2022): e2022WR033249. DOI: <https://doi.org/10.1029/2022WR033249>.
- **Type/status:** Peer-reviewed continental event study.
- **Objective and setting:** The authors compare the controls of local floods with those of spatially extensive regional floods across the contiguous United States. They ask whether storm type, antecedent wetness and snow conditions differ when high flows affect one catchment versus many catchments.
- **Outcome and method:** Gauge events are classified as local or regional using their spatial co-occurrence. Storm types are assigned from meteorological conditions, and antecedent soil moisture and snowmelt indicators are compared across event classes, regions and seasons.
- **Author-reported findings:** Regional floods are more consistently associated with wet antecedent conditions and snow-related contributions than local floods. Storm-type differences between local and regional events are present but less consistent across regions than the differences in antecedent conditions. Controls vary geographically and seasonally rather than following one national relationship.
- **Author-stated limitations:** Results depend on the definitions of local and regional events, the gauge network and large-scale meteorological and land-surface products. The spatial coverage and climate of the United States differ from South Limburg. The paper distinguishes event classes; it does not estimate substitution of one gauge for another or indoor-sensor recurrence.
- **Locators/questions:** Abstract; event and storm-type definitions; Figs. 3 and 5–11; results by region; discussion. Q09, Q14, Q15.

### JiangEtAl2022 — Jiang et al. (2022)

- **Citation:** Shijie Jiang, Emanuele Bevacqua and Jakob Zscheischler. “River Flooding Mechanisms and Their Changes in Europe Revealed by Explainable Machine Learning.” *Hydrology and Earth System Sciences* 26 (2022): 6339–6359. DOI: <https://doi.org/10.5194/hess-26-6339-2022>.
- **Type/status:** Peer-reviewed European large-sample study.
- **Objective and setting:** The paper identifies combinations of recent precipitation, antecedent precipitation and snowmelt associated with annual maximum river floods across about 1,000 European catchments and examines changes in their relative importance.
- **Outcome and method:** The analysis contains 53,968 annual flood events. An explainable machine-learning framework estimates how the three candidate drivers contribute to flood occurrence across catchments, seasons and time. Driver combinations, rather than only single dominant mechanisms, are reported.
- **Author-reported findings:** More than half of the events are associated with combinations of drivers. Recent precipitation together with wet antecedent conditions is reported as a leading combination for roughly one-third of events, while snowmelt is important in colder regions and seasons. Mechanism prevalence and its changes vary across Europe.
- **Author-stated limitations:** The selected variables cannot represent every runoff process, gridded inputs and catchment observations contain uncertainty, and feature-attribution methods describe the fitted model rather than proving causation. Annual maxima omit smaller threshold events and provide one event per catchment-year. The model is evidence about process heterogeneity, not a candidate model for this chapter.
- **Locators/questions:** Abstract; §§2.2–2.4; mechanism definitions; Figs. 2–7; limitations and conclusions. Q09, Q10.

### ZhengEtAl2023 — Zheng et al. (2023)

- **Citation:** Yanchen Zheng, Gemma Coxon, Ross Woods, Jianzhu Li and Ping Feng. “Controls on the Spatial and Temporal Patterns of Rainfall-Runoff Event Characteristics—A Large Sample of Catchments across Great Britain.” *Water Resources Research* 59 (2023): e2022WR033226. DOI: <https://doi.org/10.1029/2022WR033226>.
- **Type/status:** Peer-reviewed large-sample event study.
- **Objective and setting:** The study examines how rainfall-runoff event characteristics vary among British catchments and seasons and which climate, landscape and antecedent variables account for those patterns.
- **Outcome and method:** Continuous rainfall and flow records are separated into events. Event descriptors include rainfall depth, maximum hourly intensity, duration, runoff coefficient and response timing. Explanatory variables include antecedent soil moisture, pre-event baseflow and catchment attributes. Statistical comparisons are made across a large national gauge sample.
- **Author-reported findings:** Event response varies with both rainfall properties and pre-event catchment state. Rainfall depth and intensity, antecedent soil moisture and baseflow have differing importance for event runoff characteristics, and their relationships vary spatially and seasonally. The authors report that no single event descriptor captures the full diversity of rainfall-runoff response.
- **Author-stated limitations:** Event identification and separation choices affect the sample; national gridded rainfall and soil-moisture estimates carry error; and catchment attributes do not resolve within-catchment heterogeneity. The study concerns rainfall-runoff events broadly and does not fix a high-water threshold or distance-decay estimand for Limburg.
- **Locators/questions:** Abstract; data and event-separation sections; Table 3; §3.3; spatial and seasonal result figures; discussion. Q08, Q09, Q11.

### TramblayEtAl2023 — Tramblay et al. (2023)

- **Citation:** Yves Tramblay, Patrick Arnaud, Guillaume Artigue, Michel Lang, Emmanuel Paquet, Luc Neppel and Eric Sauquet. “Changes in Mediterranean Flood Processes and Seasonality.” *Hydrology and Earth System Sciences* 27 (2023): 2973–2987. DOI: <https://doi.org/10.5194/hess-27-2973-2023>.
- **Type/status:** Peer-reviewed regional flood-process study.
- **Objective and setting:** The authors investigate changes in flood-generating processes and seasonality at 98 gauging stations in southern France. Records average about 50 years and span 1959–2021.
- **Outcome and method:** A peaks-over-threshold sample of 5,317 floods is constructed at approximately one event per year. Independence is imposed with an area-dependent time window, (5 + \log(A)) days, plus a runoff-recession condition. Event rainfall, soil moisture and hydrograph characteristics are used to classify flood types and assess temporal change.
- **Author-reported findings:** Flood process and seasonality differ across the Mediterranean region. Soil-moisture and runoff conditions distinguish event types, and changes over time are not uniform among catchments. The study shows explicitly how declustering and antecedent state enter an event-level regional analysis.
- **Author-stated limitations:** Threshold and declustering choices affect event membership, event classifications can overlap, and soil-moisture estimates are indirect. Trend detection depends on record length and station coverage. Southern France has different hydroclimatic conditions from Limburg, so the paper supplies an event-sampling precedent rather than local parameter values.
- **Locators/questions:** Abstract; §§2.1–2.4; POT and independence rule; Figs. 3–8; trend and limitation discussion. Q10, Q16, Q17.

### MeyerEtAl2022 — Meyer et al. (2022)

- **Citation:** Judith Meyer, Malte Neuper, Luca Mathias, Erwin Zehe and Laurent Pfister. “Atmospheric Conditions Favouring Extreme Precipitation and Flash Floods in Temperate Regions of Europe.” *Hydrology and Earth System Sciences* 26 (2022): 6163–6183. DOI: <https://doi.org/10.5194/hess-26-6163-2022>.
- **Type/status:** Peer-reviewed meteorological event study.
- **Objective and setting:** The paper examines atmospheric and land-surface conditions associated with extreme precipitation and documented flash floods in central western Europe from 1981–2020.
- **Outcome and method:** The authors identify 3,835 RADKLIM precipitation events above 40 mm h⁻¹ during 2001–2020 and compare atmospheric fields with a database containing 40 flash floods linked to 37 precipitation events. Variables include humidity, convective available potential energy, wind and upper-soil moisture over antecedent periods.
- **Author-reported findings:** High lower-tropospheric moisture, instability, relative humidity and weak steering winds often accompany extreme precipitation. Wet upper soil during the preceding day can distinguish some flash-flood cases, but the authors report multiple meteorological pathways rather than one necessary combination.
- **Author-stated limitations:** The flash-flood database is non-exhaustive, some observations are not statistically independent, ERA5 is coarse relative to convective storms, and radar estimates contain artefacts and terrain-related uncertainty. The rainfall threshold defines meteorological extremes rather than receiver-gauge high-water onset.
- **Locators/questions:** Abstract; §§2.2–2.3; event definitions; Figs. 4–6; limitations and conclusions. Q20, Q22.

## Spatial dependence, synchrony and event footprints

### KeefEtAl2009 — Keef et al. (2009)

- **Citation:** Caroline Keef, Cecilia Svensson and Jonathan A. Tawn. “Spatial Dependence in Extreme River Flows and Precipitation for Great Britain.” *Journal of Hydrology* 378 (2009): 240–252. DOI: <https://doi.org/10.1016/j.jhydrol.2009.09.026>.
- **Type/status:** Peer-reviewed canonical spatial-extremes study.
- **Objective and setting:** The paper measures how dependence between extreme river flows changes with separation and compares that dependence with extreme precipitation across Great Britain. It also examines whether catchment similarity helps explain pairwise dependence.
- **Outcome and method:** The authors use a conditional spatial-extremes measure that describes the probability of an extreme at one site when another is extreme. Pairwise relationships are modelled against distance and differences in catchment characteristics. River-flow and rainfall dependence are compared at increasing event severity.
- **Author-reported findings:** Dependence generally weakens with distance but is not a function of distance alone. Catchment diversity reduces dependence in river flows relative to precipitation. The authors report that very rare river-flow extremes can be more spatially localized than less extreme high flows, so a dependence estimate at one threshold need not apply unchanged farther into the tail.
- **Author-stated limitations:** Sparse joint extremes create uncertainty at long distances and high return levels. Gauge distribution and catchment heterogeneity affect fitted relationships, and pairwise models do not capture every feature of a multivariate network. The British estimates are not direct Limburg distance coefficients.
- **Locators/questions:** Abstract; conditional-dependence definition; catchment and rainfall comparisons; distance-response figures; discussion and conclusions. Q12, Q13, Q14.

### UhlemannEtAl2010 — Uhlemann et al. (2010)

- **Citation:** Silke Uhlemann, Annegret H. Thieken and Bruno Merz. “A Consistent Set of Trans-Basin Floods in Germany between 1952–2002.” *Hydrology and Earth System Sciences* 14 (2010): 1277–1295. DOI: <https://doi.org/10.5194/hess-14-1277-2010>.
- **Type/status:** Peer-reviewed historical event-footprint study.
- **Objective and setting:** The authors build a consistent catalogue of floods affecting multiple German river basins between 1952 and 2002 and examine their spatial extent, magnitude and seasonality.
- **Outcome and method:** Daily discharge at a national gauge network is normalized to make local flows comparable. Contemporaneous high-flow episodes are grouped into trans-basin events, and spatial extent is measured by the share and arrangement of affected gauges. Events are ranked using both local magnitude and network coverage.
- **Author-reported findings:** The catalogue contains 80 trans-basin floods, of which 32 affected more than one-third of the network. Events with similar local peaks can have different spatial footprints, and broad events show distinct seasonal and hydro-meteorological patterns. The authors present joint consideration of magnitude and extent as necessary for describing national-scale floods.
- **Author-stated limitations:** Network density and changing station availability influence measured extent. Daily observations can merge or blur rapidly evolving events, while normalized gauge exceedances do not represent inundated area directly. The nationwide event-building rules operate at a larger temporal and spatial scale than a South Limburg hourly analysis.
- **Locators/questions:** Abstract; §§2.2–2.4; trans-basin event definition; event-ranking tables; spatial maps; discussion. Q12, Q15, Q18.

### BerghuijsEtAl2019 — Berghuijs et al. (2019)

- **Citation:** Wouter R. Berghuijs, Scott T. Allen, Shaun Harrigan and James W. Kirchner. “Growing Spatial Scales of Synchronous River Flooding in Europe.” *Geophysical Research Letters* 46 (2019): 1423–1428. DOI: <https://doi.org/10.1029/2018GL081883>.
- **Type/status:** Peer-reviewed continental synchrony study.
- **Objective and setting:** The paper quantifies the spatial scale over which annual river floods occur synchronously across Europe and tests whether that scale changed from 1960 to 2010.
- **Outcome and method:** Annual flood dates from more than 4,000 gauging stations are compared pairwise. Synchrony is measured from the coincidence of flood timing and related to interstation distance. The authors estimate regional spatial scales and temporal trends while examining the influence of seasonal flood timing.
- **Author-reported findings:** Synchronous flood scales differ markedly across Europe and frequently extend beyond individual river basins. The paper reports an approximately 50% increase in the average spatial scale during 1960–2010, with regional variation. Changes in flood seasonality are identified as an important contributor to the temporal pattern.
- **Author-stated limitations:** The analysis uses annual maximum dates and therefore does not retain all high-flow episodes or their magnitudes. Station density and record availability vary, and synchrony denotes timing coincidence rather than physical propagation or gauge substitutability. The continental trend analysis does not provide a local all-donor contrast for Limburg.
- **Locators/questions:** Abstract; network and synchrony definitions; European maps; temporal-trend analysis; discussion and supporting information. Q12, Q13.

### BrunnerEtAl2019 — Brunner et al. (2019)

- **Citation:** Manuela I. Brunner, Reinhard Furrer and Anne-Catherine Favre. “Modeling the Spatial Dependence of Floods Using the Fisher Copula.” *Hydrology and Earth System Sciences* 23 (2019): 107–124. DOI: <https://doi.org/10.5194/hess-23-107-2019>.
- **Type/status:** Peer-reviewed spatial-statistical case study.
- **Objective and setting:** The authors develop a multivariate model for flood dependence in ten nested catchments of the Thur basin in Switzerland. They compare local flood events with events identified across the network and examine whether river-network distance explains dependence better than straight-line distance.
- **Outcome and method:** Peaks above a high threshold are separated using a minimum time interval and recession requirement. Local exceedances are combined into 63 regional events. A Fisher copula models pairwise and higher-dimensional dependence as a function of spatial separation and catchment position.
- **Author-reported findings:** Dependence decreases with separation, and river distance can describe relationships more effectively than Euclidean distance in the nested basin. Regional event identification changes the sample relative to independent local series. The fitted copula can represent different dependence strengths within one network.
- **Author-stated limitations:** Only 63 regional events and ten gauges are available, making tail-dependence estimates uncertain. Results depend on event matching, threshold selection and distance definition. The parametric copula is presented for multivariate flood estimation; it is not required to estimate a transparent median event-minus-control gradient.
- **Locators/questions:** Abstract; §§2.2–2.4; local and regional event definitions; §§3–4; distance comparison; limitation discussion. Q12, Q13, Q18.

### QuinnEtAl2019 — Quinn et al. (2019)

- **Citation:** Niall Quinn, Paul D. Bates, Jeff Neal, Andy Smith, Oliver Wing, Chris Sampson, James Smith and Janet Heffernan. “The Spatial Dependence of Flood Hazard and Risk in the United States.” *Water Resources Research* 55 (2019): 1890–1911. DOI: <https://doi.org/10.1029/2018WR024205>.
- **Type/status:** Peer-reviewed national spatial-hazard study.
- **Objective and setting:** The paper characterizes the spatial dependence and footprints of river flooding across the conterminous United States and evaluates implications for aggregated exposure and risk.
- **Outcome and method:** More than 63,000 events from roughly 2,400 USGS gauges are grouped using temporal coincidence. Normalized flow severity is mapped across the network. Event-footprint properties and pairwise dependence are analysed in relation to distance, hydroclimate and physiographic heterogeneity, then connected to spatially distributed exposure.
- **Author-reported findings:** Flood footprints vary substantially in area, geometry and internal severity. Dependence generally declines with distance, but the rate differs across regions and catchment settings. Large aggregated losses can arise from spatially extensive events even when local return levels are not uniformly exceptional.
- **Author-stated limitations:** Gauge density is uneven; streamflow thresholds do not map one-to-one to inundation; and temporal grouping can join distinct generating systems or split long storms. National-scale dependence and exposure data cannot identify the mechanism or useful donor radius for a specific small European basin without local estimation.
- **Locators/questions:** Abstract; event construction and dependence methods; national footprint maps; distance and risk results; discussion and conclusions. Q12, Q13, Q15.

### BrunnerEtAl2020 — Brunner et al. (2020)

- **Citation:** Manuela I. Brunner, Eric Gilleland, Andy Wood, Daniel L. Swain and Martyn Clark. “Spatial Dependence of Floods Shaped by Spatiotemporal Variations in Meteorological and Land-Surface Processes.” *Geophysical Research Letters* 47 (2020): e2020GL088000. DOI: <https://doi.org/10.1029/2020GL088000>.
- **Type/status:** Peer-reviewed continental process study.
- **Objective and setting:** The authors investigate why spatial dependence among floods varies across the contiguous United States and across seasons. They separate contributions from meteorological forcing and land-surface state.
- **Outcome and method:** Concurrent flood occurrences at gauge pairs are represented with a spatial-dependence measure and related to distance. Meteorological and hydrological process indicators—including precipitation, soil moisture and snow-related conditions—are used to explain regional and seasonal variation in the dependence-distance relationship.
- **Author-reported findings:** Flood dependence declines with distance but its level and decay vary among regions and seasons. Dependence is often stronger in winter and spring. The authors report that land-surface conditions, not precipitation fields alone, are important for explaining whether floods occur jointly over space.
- **Author-stated limitations:** Dependence estimates inherit uncertainty from threshold selection, gauge records and large-scale process data. The analysis identifies associations rather than causal effects, and aggregated U.S. regions contain heterogeneous basins. A local study must estimate its own distance relationship and cannot assume one universal decay curve.
- **Locators/questions:** Abstract; event and dependence definitions; regional/seasonal results; meteorological and land-surface attribution figures; discussion. Q12, Q13, Q14.

### KemterEtAl2020 — Kemter et al. (2020)

- **Citation:** Matthias Kemter, Bruno Merz, Norbert Marwan, Sergiy Vorogushyn and Günter Blöschl. “Joint Trends in Flood Magnitudes and Spatial Extents across Europe.” *Geophysical Research Letters* 47 (2020): e2020GL087464. DOI: <https://doi.org/10.1029/2020GL087464>.
- **Type/status:** Peer-reviewed European trend study.
- **Objective and setting:** This study tests whether changes in European flood magnitude have occurred together with changes in the geographical extent of events.
- **Outcome and method:** Long river-gauge records are used to identify annual floods and their temporal co-occurrence across stations. The authors estimate trends in local flood magnitude and spatial extent and compare patterns among European regions. Hydroclimatic mechanism and seasonality are used to interpret regional differences.
- **Author-reported findings:** Magnitude and spatial extent do not change uniformly across Europe. The authors report regions where larger floods also became more spatially extensive, including parts of central Europe and the British Isles, and regions with different or weak trends. Changes are linked to regional flood-generating mechanisms rather than a continent-wide response.
- **Author-stated limitations:** Gauge coverage, record selection and the statistical detection of trends affect the map of changes. Annual maxima omit secondary events, and spatial co-occurrence is not the same as physical propagation. The study estimates multi-decadal change at continental scale rather than within-storm donor reach in South Limburg.
- **Locators/questions:** Abstract; data and event-coincidence methods; European trend maps; regional mechanism discussion; supporting information. Q12, Q15.

### Brunner2023 — Brunner (2023)

- **Citation:** Manuela Irene Brunner. “Floods and Droughts: A Multivariate Perspective.” *Hydrology and Earth System Sciences* 27 (2023): 2479–2497. DOI: <https://doi.org/10.5194/hess-27-2479-2023>.
- **Type/status:** Peer-reviewed review article.
- **Objective and setting:** The paper reviews multivariate perspectives on hydrological extremes, including event severity, spatial extent, duration, dependence and compounding drivers. Its scope is methodological and international rather than specific to one catchment.
- **Outcome and method:** Brunner organizes empirical and statistical approaches for defining multivariate events and modelling dependence. Topics include event identification, spatially compounding floods and droughts, impact relevance, copulas and other multivariate models, and nonstationarity.
- **Author-reported findings:** The review states that a univariate peak cannot describe all dimensions relevant to an extreme. Spatial extent, timing, duration and co-occurring drivers may change the consequences of events with similar local magnitude. It catalogues alternatives for event construction and dependence analysis and emphasizes alignment between the scientific question and the chosen event definition.
- **Author-stated limitations:** Multivariate models require more data than univariate analyses, dependence structures become difficult to estimate in high dimensions, and definitions of events and impact relevance are context dependent. The review does not endorse one universal spatial-transfer estimator or threshold.
- **Locators/questions:** Abstract; §§2–5; tables of event dimensions and methods; sections on spatially compounding extremes, impacts and research needs. Q12, Q15, Q19.

## Threshold events and declustering

### LangEtAl1999 — Lang et al. (1999)

- **Citation:** Michel Lang, Taha B. M. J. Ouarda and Bernard Bobée. “Towards Operational Guidelines for Over-Threshold Modeling.” *Journal of Hydrology* 225 (1999): 103–117. DOI: <https://doi.org/10.1016/S0022-1694(99)00167-5>.
- **Type/status:** Peer-reviewed canonical methodological review.
- **Objective and setting:** The article reviews practical decisions required for peaks-over-threshold analysis of hydrological extremes. It addresses event sampling rather than one river basin and compares approaches then in use in flood-frequency studies.
- **Outcome and method:** The authors examine threshold selection, independence criteria, the average number of retained events, distribution choice and estimation. They organize diagnostics and recommendations for constructing a partial-duration series and contrast its properties with annual maxima.
- **Author-reported findings:** Peaks-over-threshold sampling can retain more information about high flows than one annual maximum, particularly when records are limited. That gain depends on selecting a high-enough threshold and separating clusters so the retained peaks are approximately independent. Threshold and declustering decisions are linked rather than interchangeable preprocessing details.
- **Author-stated limitations:** No automatic rule performs best in every catchment. Estimates can be sensitive to threshold, independence criterion, seasonality, nonstationarity and sample size. The authors recommend diagnostic and sensitivity work rather than a universal event-separation interval. The paper supplies methodological reasoning, not a hydrological justification for a specific Limburg percentile or 72-hour rule.
- **Locators/questions:** Abstract; review of partial-duration series; sections on threshold choice, independence and model fitting; concluding guidelines. Q16, Q17, Q19.

### FerroSegers2003 — Ferro and Segers (2003)

- **Citation:** Christopher A. T. Ferro and Johan Segers. “Inference for Clusters of Extreme Values.” *Journal of the Royal Statistical Society: Series B (Statistical Methodology)* 65 (2003): 545–556. DOI: <https://doi.org/10.1111/1467-9868.00401>.
- **Type/status:** Peer-reviewed canonical statistical-methods article.
- **Objective and setting:** The paper develops inference for clustering in stationary extreme-value sequences without requiring the analyst to set a fixed run length before estimating cluster behaviour.
- **Outcome and method:** Inter-exceedance times above a high threshold are used to estimate the extremal index, which describes the degree of clustering. The proposed intervals estimator supports an automatic declustering scheme. Asymptotic results and bootstrap procedures are developed and examined through examples and simulation.
- **Author-reported findings:** Short inter-exceedance times identify within-cluster observations, while long gaps separate clusters. The intervals estimator can be applied before constructing cluster maxima and provides a data-based alternative to an arbitrary fixed runs parameter. The authors show how uncertainty in the extremal index can be assessed.
- **Author-stated limitations:** The theory assumes a stationary process and a sufficiently high threshold, and finite samples can make the separation between short and long intervals ambiguous. Results remain sensitive to threshold and dependence structure. The method addresses clustering within a sequence; it does not determine how events at different river gauges should be assigned to one regional storm.
- **Locators/questions:** Abstract; §§2–4; intervals estimator and automatic declustering algorithm; simulation examples; bootstrap discussion. Q17, Q19.

### Coles2001 — Coles (2001)

- **Citation:** Stuart Coles. *An Introduction to Statistical Modeling of Extreme Values.* Springer Series in Statistics. London: Springer, 2001. DOI: <https://doi.org/10.1007/978-1-4471-3675-0>.
- **Type/status:** Canonical graduate-level statistical monograph.
- **Objective and setting:** The book presents probability models and inferential tools for rare events, including block maxima, threshold exceedances, return levels, nonstationarity and dependent extremes. Its examples span environmental applications rather than one geography.
- **Outcome and method:** Coles derives generalized extreme-value and generalized Pareto models, likelihood-based inference, diagnostics and uncertainty intervals. Later chapters address temporal dependence, clustering and multivariate extremes. Worked examples show how model assumptions affect extrapolation beyond observed data.
- **Author-reported findings:** The text explains that threshold methods can use multiple extreme observations per block, while block-maxima methods trade data efficiency for a simpler sampling structure. A threshold must be high enough for the limiting approximation but low enough to leave an estimable sample. Dependence requires explicit treatment because clustered exceedances do not provide independent information.
- **Author-stated limitations:** Extreme-value inference is intrinsically uncertain because it extrapolates from scarce tail observations. Threshold choice, model diagnostics, stationarity and dependence cannot be resolved by formula alone. Parametric tail models are not automatically warranted for a descriptive event-contrast chapter; the book is retained for the sampling assumptions behind event definitions.
- **Locators/questions:** Chapters 3–5 on threshold models and inference; Chapter 5 on diagnostics; chapters on nonstationarity and dependence. Q16, Q19.

## Rainfall and discharge measurement

### BartelsEtAl2004 — Bartels et al. (2004)

- **Citation:** Hella Bartels, Elmar Weigl, Thomas Reich, Peter Lang, Andreas Wagner, Otfried Kohler and Nicole Gerlach. *Projekt RADOLAN: Routineverfahren zur Online-Aneichung der Radarniederschlagsdaten mit Hilfe von automatischen Bodenniederschlagsstationen (Ombrometer). Abschlussbericht.* Deutscher Wetterdienst, 2004.
- **Official record:** <https://www.dwd.de/DE/leistungen/radolan/radolan_info/abschlussbericht_pdf.pdf?__blob=publicationFile&v=2>
- **Type/status:** Official DWD technical report and canonical product documentation.
- **Objective and setting:** The report documents the RADOLAN procedure developed to combine Germany’s weather-radar composites with automated precipitation-gauge observations for operational quantitative precipitation estimation.
- **Outcome and method:** Radar reflectivity is converted to precipitation, assembled into national composites and adjusted using gauge observations. The documented system produces five-minute radar fields and hourly gauge-adjusted RW totals on a national 1 km grid. The report describes quality control, spatial adjustment and product formats.
- **Author-reported findings:** Gauge adjustment corrects important systematic and event-dependent differences between unadjusted radar estimates and ground observations. The product preserves radar’s spatial coverage while using gauges to constrain accumulations. Quality indicators and missing-value codes are part of the product rather than ordinary rainfall values.
- **Documented limitations:** Radar blockage, clutter, attenuation, bright-band effects, changing radar calibration and sparse or delayed gauge data can affect the field. An individual grid cell is an areal estimate, not a point-gauge observation. The report documents the operational method current in 2004; later reprocessed RADKLIM products and corrections require their own version records.
- **Locators/questions:** Product overview; radar composite and gauge-adjustment chapters; quality-control sections; grid and binary-format appendices. Q20.

### WinterrathEtAl2018 — Winterrath et al. (2018)

- **Citation:** Tanja Winterrath, Christoph Brendel, Mario Hafer, Thomas Junghänel, Anna Klameth, Katharina Lengfeld, Ewelina Walawender, Elmar Weigl and Andreas Becker. *Radarklimatologie aus angeeichten Niederschlagsstundensummen Version 2017.002: Gerasterte Niederschlagswerte für Deutschland.* DWD dataset v2017.02, 2018. DOI: <https://doi.org/10.5676/DWD/RADKLIM_RW_V2017.002>.
- **Type/status:** Versioned official scientific dataset.
- **Objective and setting:** RADKLIM reprocesses the RADOLAN archive to provide a spatially and temporally consistent radar-based rainfall climatology for Germany. It is a data product, not a study of flood response.
- **Data and method:** Hourly RW precipitation totals derive from radar estimates adjusted to ground-gauge observations. The grid is 1 km × 1 km in a polar-stereographic projection. Version 2017.002 originally covers 2001–2017; the official landing page records later annual extensions and says the period used must be reported.
- **Provider-reported characteristics:** The version adds extensive correction of radar artefacts relative to its predecessor and supplies national gridded hourly accumulations suitable for spatial aggregation. Five-minute YW rates are quasi-adjusted using RW information.
- **Provider-documented limitations:** The landing page records missing or corrupt files subsequently supplied in a `supplement` directory and specifically warns that 2021 NetCDF data are erroneous unless replaced by corrected files. Extensions are not all part of the original DOI-referenced package. Product version, file origin, missing codes, projection and exact analysis years therefore remain necessary provenance.
- **Locators/questions:** Official DOI landing page, especially title/citation, abstract, update chronology, spatial/temporal coverage and supplement warning. Q20.

### McMillanEtAl2012 — McMillan et al. (2012)

- **Citation:** Hilary McMillan, Tobias Krueger and Jim Freer. “Benchmarking Observational Uncertainties for Hydrology: Rainfall, River Discharge and Water Quality.” *Hydrological Processes* 26 (2012): 4078–4111. DOI: <https://doi.org/10.1002/hyp.9384>.
- **Type/status:** Peer-reviewed canonical uncertainty review.
- **Objective and setting:** The article reviews the magnitude and structure of observational uncertainty in hydrological rainfall, discharge and water-quality data and proposes benchmark ranges for common measurement situations.
- **Outcome and method:** Published experiments and uncertainty estimates are organized by variable, instrument and hydrological condition. The authors distinguish random error, systematic bias, representativeness and uncertainty introduced when measurements are transformed, interpolated or extrapolated.
- **Author-reported findings:** Rainfall uncertainty changes with instrument, intensity and spatial aggregation, while discharge uncertainty combines stage measurement with rating-curve and cross-section uncertainty. Errors can be small under well-gauged ordinary conditions but exceed tens of percent in difficult or extreme conditions. The review emphasizes that uncertainty is often heteroscedastic and temporally correlated rather than a constant error band.
- **Author-stated limitations:** Published estimates are uneven across instruments, sites and flow regimes, and the proposed ranges cannot replace station-specific assessment. Many studies report precision but not bias or representativeness. The benchmarks do not determine whether a damaged July 2021 gauge supports an exact onset; they identify what must be checked in the source record.
- **Locators/questions:** Abstract; rainfall and discharge benchmark tables; sections on spatial representativeness, rating curves and uncertainty communication; conclusions. Q07, Q20, Q21.

### CoxonEtAl2015 — Coxon et al. (2015)

- **Citation:** Gemma Coxon, Jim Freer, Ida K. Westerberg, Thorsten Wagener, Ross Woods and P. J. Smith. “A Novel Framework for Discharge Uncertainty Quantification Applied to 500 UK Gauging Stations.” *Water Resources Research* 51 (2015): 5531–5546. DOI: <https://doi.org/10.1002/2014WR016532>.
- **Type/status:** Peer-reviewed large-sample measurement study.
- **Objective and setting:** The authors develop and apply a consistent method for estimating discharge uncertainty across 500 gauging stations in England and Wales, where station-specific information and rating quality differ.
- **Outcome and method:** Stage-discharge rating information, gauging observations and station descriptors are used in a nonparametric LOWESS framework. The method produces discharge estimates and uncertainty bounds for low, medium and high-flow conditions and classifies the evidential support available at each station.
- **Author-reported findings:** Uncertainty varies strongly among stations and through the flow range. High-flow uncertainty increases when ratings extend beyond direct gaugings or when controls change. A network-wide analysis that treats published discharge as exact can therefore give unequal confidence to different gauges and events.
- **Author-stated limitations:** The framework depends on the quantity and quality of available stage-discharge measurements and cannot recover information absent from station records. Where the rating is poorly constrained, uncertainty intervals may themselves be uncertain. The study addresses uncertainty around recorded flow; it does not repair a gauge that stops during a peak or justify inventing an exact event time.
- **Locators/questions:** Abstract; §§2–3; LOWESS uncertainty framework; network result maps; high-flow examples; discussion and conclusions. Q07, Q21.

### KiangEtAl2018 — Kiang et al. (2018)

- **Citation:** Julie E. Kiang, Chris Gazoorian, Hilary McMillan, Gemma Coxon, Jérôme Le Coz, Ida K. Westerberg, Arnaud Belleville, Damien Sevrez, Anna E. Sikorska, Asgeir Petersen-Øverleir, Trond Reitan, Jim Freer, Benjamin Renard, Valentin Mansanarez and Robert Mason. “A Comparison of Methods for Streamflow Uncertainty Estimation.” *Water Resources Research* 54 (2018): 7149–7176. DOI: <https://doi.org/10.1029/2018WR022708>.
- **Type/status:** Peer-reviewed intercomparison study.
- **Objective and setting:** The paper compares seven methods for quantifying uncertainty in streamflow derived from stage-discharge ratings. Three gauging stations with different channel controls and data situations serve as common test cases.
- **Outcome and method:** Participating methods use different assumptions about stage error, discharge-measurement error, rating form, residual structure and temporal change. Each method generates discharge uncertainty across the rating range, allowing comparison of interval width and behaviour under extrapolation.
- **Author-reported findings:** Estimated uncertainty differs materially among methods, especially at high flows and beyond measured gaugings. Differences can be traced to assumptions as well as to data. The authors do not identify one method as universally best; they call for matching the uncertainty method to station characteristics and the intended use.
- **Author-stated limitations:** Three stations cannot represent all rating controls, and the true continuous discharge is unavailable for direct validation. Methods may omit changing channel geometry, hysteresis or other errors. The intercomparison supports explicit station-level QA but does not transform censored July 2021 evidence into an observed peak.
- **Locators/questions:** Abstract; method-comparison design; station descriptions; uncertainty plots; discussion of assumptions and recommendations. Q07, Q21.

## Long-record public weather

### MunozSabaterEtAl2021 — Muñoz-Sabater et al. (2021)

- **Citation:** Joaquín Muñoz-Sabater, Emanuel Dutra, Anna Agustí-Panareda, Clément Albergel, Gabriele Arduini, Gianpaolo Balsamo, Souhail Boussetta, Margarita Choulga, Shaun Harrigan, Hans Hersbach, Brecht Martens, Diego G. Miralles, María Piles, Nemesio J. Rodríguez-Fernández, Ervin Zsoter, Carlo Buontempo and Jean-Noël Thépaut. “ERA5-Land: A State-of-the-Art Global Reanalysis Dataset for Land Applications.” *Earth System Science Data* 13 (2021): 4349–4383. DOI: <https://doi.org/10.5194/essd-13-4349-2021>.
- **Type/status:** Peer-reviewed data-description article.
- **Objective and setting:** The article documents the production and evaluation of ERA5-Land, a global land-surface reanalysis driven by downscaled ERA5 meteorological forcing. The product is designed to give temporally consistent land and near-surface fields over a multi-decadal period.
- **Data and method:** ERA5 atmospheric forcing is interpolated from roughly 31 km to the ERA5-Land grid, with elevation correction for near-surface thermodynamic variables, and used to drive the land model offline. ERA5-Land has hourly temporal resolution and approximately 9 km horizontal resolution. Evaluation uses in-situ, model and satellite reference datasets, mainly from 2000–2018.
- **Author-reported findings:** The authors report advantages from the finer grid for several water-cycle fields and broadly similar energy-cycle performance to ERA5. They present continuity, hourly resolution and a fixed grid as product strengths for hydrological and land applications.
- **Author-stated limitations:** ERA5-Land remains a model-based reanalysis rather than a direct station observation. Small-scale heterogeneity is unresolved, atmospheric forcing is interpolated from coarser ERA5 fields, and evaluation coverage is incomplete and variable-specific. Performance findings for land variables do not constitute a local validation of Limburg temperature, humidity or pressure.
- **Locators/questions:** Abstract; §§2–4; §6; data-access statement. Q23.

### CopernicusERA5Land2019 — Copernicus Climate Change Service (2019)

- **Citation:** Copernicus Climate Change Service. *ERA5-Land Hourly Data from 1950 to Present.* Climate Data Store dataset, first published 2019 and continuously updated. DOI: <https://doi.org/10.24381/cds.e2161bac>.
- **Type/status:** Versioned official public reanalysis dataset and product record.
- **Objective and setting:** The product provides globally complete, hourly land and near-surface variables on a regular latitude–longitude grid. The present Climate Data Store record covers 1950 to near-present and identifies the product as ERA5-Land rather than direct meteorological observations.
- **Data and method:** The land component of ERA5 is replayed at 0.1° resolution using ERA5 atmospheric forcing. Available fields include 2 m temperature, 2 m dew-point temperature and surface pressure. The gridded download service allows a fixed geographic subset and period to be requested in NetCDF or GRIB format.
- **Provider-reported characteristics:** The fixed grid and multi-decadal hourly record support consistent extraction across national borders and periods. Observations affect the product indirectly through ERA5 atmospheric forcing; they are not assimilated directly into the offline ERA5-Land run.
- **Provider-documented limitations:** The fields are numerical-model estimates with uncertainty, not station measurements. The provider states that uncertainty generally increases backward in time as the observing basis for the forcing becomes thinner. A 0.1° cell cannot represent building-scale weather or all topographic variation in a small tributary catchment. Dataset update date, requested variables, grid bounds and file hashes remain necessary provenance.
- **Locators/questions:** Official overview, data description, variables, temporal/spatial coverage, licence and DOI record. Q23.

## Contemporary operational-AI context

### ProvinceLimburgDeepWaive2026 — Province of Limburg (2026)

- **Citation:** Province of Limburg. *Predicting floods in the Selzerbeek catchment area using DeepWaive.* Dutch Algorithm Register, last changed 6 August 2026. <https://algoritmes.overheid.nl/en/algoritme/pv31/99467265/predicting-floods-in-the-selzerbeek-catchment-area-using-deepwave>.
- **Type/status:** Official algorithm-register record for a research and test system; not a peer-reviewed performance evaluation.
- **Objective and setting:** The Province is testing whether a physics-based AI model trained on hydraulic simulations can generate 48-hour, two-dimensional flood-depth and flood-development products for the Selzerbeek catchment more quickly than conventional numerical models. Listed operational inputs include five-minute RADOLAN and KNMI radar, deterministic ICON-D2 precipitation forecasts, AHN-derived terrain, land use, water-system geometry and Limburg Water Board level/discharge observations.
- **Provider-reported status:** The project runs from March 2026 to February 2027. The register explicitly states that the model remains under research and has not been used for warnings or crisis management.
- **Use in this chapter:** Contemporary institutional context in the case geography. It demonstrates the evidentiary boundary between producing rapid flood information and authorizing an operational warning. It also identifies potentially relevant public-data and institutional interfaces.
- **Limitations:** The register supplies no independent validation results and no Chapter 1 outcome. DeepWaive is not a comparator or input to the retrospective recurrence analysis.
- **Locators/questions:** Goal and impact; operations/data; technical design; responsible-use statement. Q24.

### LiEtAl2026ResponsibleModelling — Li et al. (2026)

- **Citation:** Kailong Li, Saman Razavi, Holger R. Maier, Markus Hrachowitz, Ehsan Nabavi, Natasha Harvey, Khaled Akhtar and Fisaha Unduche. “When Are AI Models Ready for Deployment? Reassessing Google's Global AI Flood Forecasting System Through the Lens of Responsible Modelling.” *Journal of Hydrology X* 30 (2026): 100215. DOI: <https://doi.org/10.1016/j.hydroa.2026.100215>.
- **Type/status:** Peer-reviewed critical assessment.
- **Objective and method:** The authors reassess claims of operational readiness across predictive accuracy, timeliness, extreme-event characterization and benchmarking, emphasizing sensitivity to evaluation definitions and the intended operating environment.
- **Use in this chapter:** Supports strict separation of retrospective association from prediction, warning value and deployment readiness. It reinforces the need to anchor event definitions to observations and disclose the consequences of timing and threshold choices.
- **Limitations:** The assessment concerns a global AI forecasting system, not Limburg public-signal recurrence. Its disputed performance estimates are not transferred to this chapter.
- **Locators/questions:** Framework and §§2–3; deployment-readiness discussion. Q24.
