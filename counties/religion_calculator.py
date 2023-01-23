import pandas as pd
from objects import districts

print("Running religion calculations")


# code functions
def cd_code_formula(state, seat="N/A"):
    if seat == "N/A":
        return f'{state.lower().replace(" ", "")}'
    else:
        if len(seat) == 1:
            seat = f'0{seat}'
        return f'{state.lower().replace(" ", "")}{seat}'


def county_code_formula(state, county):
    return (county.lower()).replace(" ", "") + cd_code_formula(state)


# convert districts to codes
district_codes = []
code_to_state = {}
code_to_seat = {}
for district in districts:
    cd_code = cd_code_formula(district["State"], district["Seat"])
    district_codes.append(cd_code)
    code_to_state[cd_code] = district["State"]
    code_to_seat[cd_code] = district["Seat"]

# read CSVs
county_split_raw_data = pd.read_csv("counties/counties_to_cds_daily_kos.csv").to_dict(orient="records")
religion_raw_data = pd.read_csv("counties/county_religion_data_arda.csv").to_dict(orient="records")

# start processing CSV data
cd_religion_data = {}
religion_data = {}
cd_populations = {}
religion_group_names = {}
for district in district_codes:
    cd_religion_data[district] = {"Total Adherents": 0, "Total Non-adherents": 0}
    cd_populations[district] = 0
# get religion data transposed to counties
for county_group in religion_raw_data:
    county = county_group["COUNTY NAME"]
    state = county_group["STATE NAME"]
    county_code = county_code_formula(state, county)
    [county_group.pop(key) for key in
     ["FIPS", "COUNTY NAME", "STATE NAME"]]  # strip data to only county level group data
    group_code = county_group["GROUP CODE"]  # use instead of group name
    group_name = county_group["GROUP NAME"]
    adherents = county_group["ADHERENTS"]
    # add group id to group names if not already accounted for
    religion_group_name_lists = list(religion_group_names.values())
    if group_code not in religion_group_name_lists:
        religion_group_names[group_code] = group_name
    # add counties to religion data
    try:
        religion_data[county_code][group_code] = adherents
    except KeyError:
        religion_data[county_code] = {group_code: adherents}
# add religion groups to cd dicts
for religion in religion_group_names:
    for district in cd_religion_data:
        cd_religion_data[district][religion] = 0
# aggregate county religion data to CDs
for split_county in county_split_raw_data:
    cd_number = split_county["CD"]
    state = split_county["State"]
    county = split_county["Geography"]
    percent_of_county = float(split_county["Percentage of County"].replace("%", ""))/100
    # get constituency codes
    district_code = cd_code_formula(state, str(cd_number))
    county_code = county_code_formula(state, county)
    # add county population to CD population
    county_split_population = split_county["Population"]
    cd_populations[district_code] += county_split_population
    # get religion data and add to CD
    ignored_counties = ["alpinecountycalifornia", "lovingcountytexas"]  # these 2 counties have no data, idk why Alpine has no data
    if county_code not in ignored_counties:
        county_religion_data = religion_data[county_code]
        for group in county_religion_data:
            adherents = county_religion_data[group]*percent_of_county
            cd_religion_data[district_code][group] += adherents
            cd_religion_data[district_code]["Total Adherents"] += adherents
            cd_religion_data[district_code]["Total Non-adherents"] += adherents*-1
# convert dictionary to dataframe and save dataframe to csv
cd_religion_data_csv_ready = []
for district in cd_religion_data:  # make sure that index column is named properly
    raw_cd_data = cd_religion_data[district]
    raw_cd_data["District Code"] = district
    raw_cd_data["State"] = code_to_state[district]
    raw_cd_data["Seat"] = code_to_seat[district]
    raw_cd_data["Total Non-adherents"] += cd_populations[district]
    raw_cd_data["Total CD Population"] = cd_populations[district]
    cd_religion_data_csv_ready.append(raw_cd_data)
# make column list so that percents can be produced
all_columns = ["District Code", "State", "Seat",
               "Total CD Population", "Total Adherents",
               "Total Non-adherents"]
religion_columns = ["Total CD Population", "Total Adherents",
                    "Total Non-adherents"]
for religion in religion_group_names:
    all_columns.append(religion)  # add religion to column names
    religion_columns.append(religion_group_names[religion])  # add religion name to column names
religion_dataframe = pd.DataFrame(cd_religion_data_csv_ready, columns=all_columns)
for religion in religion_group_names:  # change column ids to religion names
    religion_name = religion_group_names[religion]
    religion_dataframe.rename(columns={religion: religion_name}, inplace=True)
religion_dataframe = religion_dataframe.to_dict(orient="records")
for district in religion_dataframe:  # add percentage column for religions
    for column in religion_columns:
        total_cd_adherents = district[column]
        total_cd_population = district["Total CD Population"]
        district[column+" %"] = total_cd_adherents/total_cd_population
religion_dataframe = pd.DataFrame(religion_dataframe)
religion_dataframe.set_index('District Code', inplace=True)
religion_dataframe.to_csv("religion_data_118th_congress.csv")  # save to CSV - everything's completed now
print("Religion calculations complete; saved to religion_data_118th_congress.csv")
