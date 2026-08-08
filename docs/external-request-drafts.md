# External Request Drafts

Status: prepared 2026-08-08; **not sent**. Replace bracketed text, attach the
UNU-MERIT affiliation/signature and preserve each sent message and reply with
the raw delivery.

## 1. Jan-Philipp Viefhues / thesis data holder

**Subject:** Request for original Kerkrade IoT data used in the 2022 thesis

Dear Jan-Philipp,

I am a PhD researcher at UNU-MERIT developing a dissertation chapter that
follows your Kerkrade thesis and E. Eryilmaz's subsequent paper. The chapter
asks whether the indoor CO2 response observed around July 2021 recurs during
later independently defined high-water episodes, while separating it from
public hydrometeorological conditions.

Could you share, or direct me to the holder of, the original Kerkrade IoT data
covering approximately 25 August 2020 through 1 September 2021? The essential
variables are indoor CO2 and air pressure. Temperature, relative humidity and
other recorded channels would also be useful if they are part of the same
export.

To reproduce the 2021 record responsibly, I would also need whatever is
available on:

- native timestamp resolution and timezone;
- device and sensor model or identifier;
- calibration, replacement or relocation history;
- whether automatic baseline correction (ABC) was enabled for CO2;
- whether exported values were already processed or aggregated;
- missing-value, duplicate and hourly-aggregation rules used in the thesis;
- any data-use or citation conditions.

Raw minute-level data are preferred, but a documented hourly export would be
valuable if the native files are no longer available. I will preserve the
original delivery, document all transformations and will not treat the 2021
high-water onset as exact where the gauge evidence is uncertain.

Thank you,

[name and UNU-MERIT signature]

## 2. Waterschap Limburg historical discharge

**To:** `info@waterschaplimburg.nl`
**Subject:** Academic information request: historical tributary discharge and
gauge metadata

Dear Waterschap Limburg,

I am a PhD researcher at UNU-MERIT studying which public hydrometeorological
signals recur before high-water episodes across Limburg tributaries. The public
measurement endpoint available to me contains only a rolling record beginning
in August 2024. I am therefore requesting an academic release of the longer
historical discharge archive and its quality metadata.

Could you provide the full available discharge history, preferably at native
resolution, for natural tributary gauges including:

- Geul: Cottessen, Hommerich and Meerssen;
- Worm/Wurm: Rimburg;
- Geleenbeek: Brommelen, Munstergeleen, Millen and Oud-Roosteren;
- Eyserbeek, Gulp, Selzerbeek and Voer;
- enough additional natural tributaries to assess a cohort of at least ten
  distinct watercourses with ten common years.

For each gauge, please include or identify:

1. station identifier, coordinates, watercourse and relocation history;
2. units and timezone/DST convention;
3. native sampling and aggregation convention;
4. the meaning of absent timestamps, missing codes and zero/sentinel values;
5. validation flags and rating-curve periods or revisions;
6. July 2021 damage, failure or unreliable-data intervals and any evidence that
   bounds high-water onset;
7. current and historical crisis-plan Fase thresholds at their exact designated
   gauges, if available;
8. licence, citation and redistribution conditions.

This is an information request for academic analysis rather than a request for
personal data. Files in their existing native format are preferable to a newly
prepared summary. I will preserve the source files, document quality flags and
leave missing values missing unless the source convention explicitly supports
another treatment.

Thank you for directing this request to the appropriate water-information or
hydrology team.

Kind regards,

[name and UNU-MERIT signature]

Waterschap's official information-request page lists `info@waterschaplimburg.nl`
and 088 88 90 100: <https://open.waterschaplimburg.nl/wet-open-overheid>.

## 3. LANUK verified-discharge semantics

**To:** `poststelle@lanuk.nrw.de`
**Routing request:** Fachbereich 51 Hydrologie / Pegelwesen Region Süd
**Subject:** Rückfrage zum Zeitstempel- und Lückenkonzept der geprüften
Abflussdaten

Sehr geehrte Damen und Herren,

ich untersuche im Rahmen einer Promotion an der UNU-MERIT die Übertragbarkeit
hydrometeorologischer Signale vor Hochwasserereignissen im grenznahen
Rur-Wurm-Gebiet. Dafür prüfe ich die veröffentlichten, geprüften
Abflusszeitreihen aus dem OpenGeodata-NRW-Angebot.

Die CSV-Dateien enthalten je nach Pegel unregelmäßige Zeitstempel, teilweise
außerhalb des 15-Minuten-Rasters. In der veröffentlichten Dokumentation zu
HYGON finde ich keine eindeutige Definition für die Zeitstempel der geprüften
Abflussarchive. Könnten Sie bitte folgende Punkte klären?

1. Ist jede CSV-Zeile eine einzelne Beobachtung oder handelt es sich um eine
   komprimierte Stufen-/Änderungszeitreihe?
2. Bedeutet ein fehlender Zeitstempel eine Datenlücke, oder bleibt der letzte
   Wert bis zum nächsten Zeitstempel gültig? Falls ja: für welche maximale
   Dauer?
3. Welche Qualitätsprüfung und welche Abflusstafel gilt für die veröffentlichten
   Werte, und wie werden Revisionen gekennzeichnet?
4. Welche Codes oder Regeln gelten für fehlende Werte, Nullwerte und ungültige
   Zeiträume?
5. Gibt es dokumentierte Ausfall- oder Unzuverlässigkeitszeiträume im Juli 2021
   für die Pegel 2828300000200 (Herzogenrath 1), 2828400000200
   (Herzogenrath 2), 2828890000200 (Honsdorf) und 2828900000200 (Randerath)?

Ich möchte insbesondere vermeiden, eine komprimierte Zeitreihe fälschlich als
Messausfall zu interpretieren oder umgekehrt nicht beobachtete Stunden
fortzuschreiben. Ein vorhandenes Datenwörterbuch oder ein Hinweis auf die
zuständige Fachperson wäre daher sehr hilfreich.

Mit freundlichen Grüßen

[Name und UNU-MERIT-Signatur]

The public LANUK materials identify Fachbereich 51 as Hydrologie and list the
central address `poststelle@lanuk.nrw.de`:
<https://www.lanuk.nrw.de/fileadmin/lanuv/service/orgaplan/orgaplan.pdf>.
