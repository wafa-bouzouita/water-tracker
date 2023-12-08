import matplotlib.pyplot as plt
from water_tracker import WaterTracker

def main():
    # Replace "" with your actual API key
    api_key = ""
    indicateurs = ["nappes", "pluviométrie", "nappes profondes"]

    wt = WaterTracker(api_key)

    # If you haven't built station data and downloaded all timeseries yet uncomment the following lines to do so
    #wt.build_stations_data()
    #wt.download_all_timeseries()

    # For each indicator, load existing data and generate the plot
    for indicateur in indicateurs:
        # Comment the following line if you don't want to recalculate standardized indicators on each run
        wt.process(indicateur=indicateur)

        # Load existing data
        wt.load()

        # Generate the plot for drought distribution in France
        df_levels = wt.plot_counts_france(indicateur=indicateur)

        # Show the plot
        plt.show()

if __name__ == "__main__":
    main()
