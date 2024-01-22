from RestrictionEauClass import *

zone_alerte_commune_url = (
    "https://www.data.gouv.fr/fr/datasets/r/25cfc138-313e-4e41-8eca-d13e3b04ca62"
)

path_corres_commune_insee = "./data/correspondance-code-insee-code-postal.csv"

dataset_id_for_year = {
    2023: '782aac32-29c8-4b66-b231-ab4c3005f574',
    2022: '0fee8de1-c6de-4334-8daf-654549e53988',
    2021: 'c23fe783-763f-4669-a9b7-9d1d199fcfcd',
    2020: 'd16ae5b1-6666-4caa-930c-7993c4cd4188',
    2019: 'ed2e6cfa-1fe7-40a6-95bb-d9e6f99a78a0',
    2018: '8ba1889e-5496-47a6-8bf3-9371086dd65c',
    2017: 'ab886886-9b64-47ca-8604-49c9910c0b74',
    2016: 'fbd87d0b-a504-49e2-be6e-66a96ca4e489',
    2015: '98cb1f80-f296-4eae-a0b3-f236fc0b9325',
    2014: 'c68362d9-93ff-46bc-99a6-35d506855dae',
    2013: 'f9c1da33-19f4-499d-88cc-b3c247484215',
    2012: '43864992-e79b-449e-9d7d-93dad9b9df59',
    2011: '227149be-cd8b-4e59-a1a9-0840ef7f0a24',
    2010: 'd6cb1826-6cc8-4709-85fd-433db23aa951'
}


cl_month = RestrictionEau()
# To Do add comments
cl_month.process(2022, 2024, filter_per_month=True, path_corres_commune_insee=path_corres_commune_insee,
                 dataset_id_for_year=dataset_id_for_year, zone_alerte_commune_url=zone_alerte_commune_url)

cl_month.plot_only_restriction_data(2023)
