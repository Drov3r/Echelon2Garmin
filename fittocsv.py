from fit_tool.fit_file import FitFile


def main():
    """ The following code reads all the bytes from a FIT formatted file and then decodes these bytes to
        create a FIT file object. We then convert the FIT data to a human-readable CSV file.
    """
    path = '164630be8c534bf9b09695089fe67457_30_min_Power_Zone_Endurance_Pop_Ride_with_Sam_Yo.fit'
    fit_file = FitFile.from_file(path)

    out_path = 'Example.csv'
    fit_file.to_csv(out_path)


if __name__ == "__main__":
    main()
