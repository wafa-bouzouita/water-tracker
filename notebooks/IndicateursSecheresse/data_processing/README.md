# watertracker

### Create a token access for imageau
Go to https://api.emi.imageau.eu/doc and use the /auth/login to create your api key.

### Create a WaterTracker object
```
wt = WaterTracker(your_api_key)
```

### Make sure you have fresh timeseries
```
wt.download_all_timeseries()
```
This will download or update all timeseries in the folder `data/timeseries/`. Each timeseries is stored in a .csv file. This step takes some times.


### Process the data
Compute standardized indicator (SPI for rain level, SPLI for other groundwater levels). All data will be saved.
```
indicateur = "pluviométrie" # can be also "nappes" or "nappes profondes"
wt.process(indicateur)
```

### Create plots
Once data has been processed, you can use them to create the plots.
```
wt.load()
wt.plot_counts_france(indicateur=indicateur)
```
They will be stored as .pdf file in the `images/` folder
