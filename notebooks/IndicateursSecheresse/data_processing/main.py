from water_tracker import WaterTracker

def main():
    api_key = ""
    indicateur = "nappes profondes"

    wt = WaterTracker(api_key)
    # First:
    #wt.process(indicateur=indicateur)
    
    # Then
    wt.load()
    wt.plot_counts_france(indicateur=indicateur)
    

if __name__ == "__main__":
    main()
