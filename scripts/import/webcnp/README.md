# WebCNP pipeline

This set of scripts requests and uploads from UPenn's Computerized NeuroPsychological (CNP) test battery.

## Script description

The script that invokes all of the pipeline steps is `cnp2redcap`, which invokes the following scripts:

1. `get_results_api` requests the results from the Penn API into a temporary directory,
2. `csv2redcap` processes the CSVs in that temporary directory and uploads them to the "Imported from PennCNP" project,
3. `update_summary_forms` propagates the data from "Imported from PennCNP" project to the "Data Entry" project.

In the cron, `cnp2redcap` is invoked with `-p --last-3-months`.

## Debugging notes

- For `get_results_api`, you'll have to provide a mandatory `out_dir` into which it scrapes its results. I recommend a pre-created `/tmp/` subdirectory.
- For `csv2redcap`, you'll need a pre-scraped file; to get this, see previous point.

## Transition from Webscraped PennCNP to API Request

In 2023 Penn made a transition from their prior interface to now using a software they developed called ProcTrack (the NCANDA project does not use this). In this time we transitioned to using their API protocol to get the data needed. Also, two fundamental updates that came along with that.
1. They changed the test session id variable from 5 digits to 7 so we now have to map between the previous id's to their new value.
2. The general test status variable no longer is created, we only have access to the {test_name}_system_status variables. So those are now what are used as the default incoming test status variables.

## Transition from PennCNP to WebCNP

In 2020, a 2.0 version was released and transitioned to. `NCANDA_Survey_Codebook.csv` holds the different variables and the mapping from the old survey (`evioni_var`) to the new survey (`survey_var`). This required changes in primarily `csv2redcap`.

There's no guarantee that IDs remain unique between versions 1.0 and 2.0, but the subject IDs include dates, so even if two collections for subject A-99999-X-9 are numbered 80000, they'd be called A-99999-X-9-2022-01-01-80000 and A-99999-X-9-2019-01-01-80000.
