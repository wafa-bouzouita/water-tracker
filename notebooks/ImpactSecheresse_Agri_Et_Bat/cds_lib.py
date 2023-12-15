from zipfile import ZipFile
import cdsapi

def get_data_init():
    c = cdsapi.Client()

    c.retrieve(
        'satellite-soil-moisture',
        {
            'variable': 'surface_soil_moisture',
            'type_of_sensor': 'active',
            'time_aggregation': 'month_average',
            'year': [
                '2013', '2014', '2015',
                '2016', '2017', '2018',
                '2019', '2020', '2021',
                '2022',
            ],
            'month': [
                '01', '02', '03',
                '04', '05', '06',
                '07', '08', '09',
                '10', '11', '12',
            ],
            'day': '01',
            'type_of_record': 'cdr',
            'version': 'v202212',
            'format': 'zip',
        },
        'data/download.zip')

    with ZipFile('data/download.zip') as myzip:
        myzip.extractall('data')


def get_data_2023():
    c = cdsapi.Client()
    c.retrieve(
        'satellite-soil-moisture',
        {
            'variable': 'surface_soil_moisture',
            'type_of_sensor': 'active',
            'time_aggregation': 'month_average',
            'year': '2023',
            'month': [
                '01', '02', '03',
                '04', '05', '06',
                '07', '08', '09',
                '10',
            ],
            'day': '01',
            'type_of_record': 'icdr',
            'version': 'v202012',
            'format': 'zip',
        },
        'data_2023/download.zip')

    with ZipFile('data_2023/download.zip') as myzip:
            myzip.extractall('data_2023')

#get_data_init()
#get_data_2023()


