import pandas as pd
from objects import districts, us_state_to_abbrev

print("Running urbanization calculations")
pop_types = ["Urban", "Suburban", "Rural"]


# code functions
def cd_code_formula(state, seat="N/A"):
    if seat == "N/A":
        return f'{state.lower().replace(" ", "")}'
    else:
        if len(seat) == 1:
            seat = f'0{seat}'
        return f'{state.lower().replace(" ", "")}{seat}'


def alt_code_formula(state, seat):
    return f'{us_state_to_abbrev[state]}-{seat}'


def county_code_formula(state, county):
    return (county.lower()).replace(" ", "") + cd_code_formula(state)


# convert districts to codes
district_codes = []
code_to_state = {}
code_to_seat = {}
tract_districts_to_codes = {}
for district in districts:
    cd_code = cd_code_formula(district["State"], district["Seat"])
    district_codes.append(cd_code)
    code_to_state[cd_code] = district["State"]
    code_to_seat[cd_code] = district["Seat"]
    alt_code = alt_code_formula(district["State"], district["Seat"])
    tract_districts_to_codes[alt_code] = cd_code

# read CSVs
tract_split_raw_data = pd.read_csv("2010_census_tracts.csv").to_dict(orient="records")
urbanization_raw_data = pd.read_csv("2010_urbanization_data.csv").to_dict(orient="records")

# start processing CSV data
cd_urbanization_data = {}
tract_urbanization_data = {}
for district in district_codes:
    cd_urbanization_data[district] = {"Urban Pop.": 0, "Suburban Pop.": 0, "Rural Pop.": 0}
# get tract urbanization data saved to dict
for tract in urbanization_raw_data:
    tract_id = tract["GEOID"]
    tract_urban = tract["UPSAI_urban"]
    tract_suburban = tract["UPSAI_suburban"]
    tract_rural = tract["UPSAI_rural"]
    tract_urbanization_data[tract_id] = {"Urban": tract_urban, "Suburban": tract_suburban,
                                         "Rural": tract_rural}
# finalized data collection
for tract in tract_split_raw_data:
    tract["CD"] = tract["CD"].replace("-AL", "-1")
    tract_cd = tract_districts_to_codes[tract["CD"]]
    percent_of_tract = float(tract["Split Tract Area"])/float(tract["Tract Area"])
    population = tract["Tract Population"]*percent_of_tract
    tract_id = tract["Tract GEOID"]
    try:
        if population > 10:
            tract_data = tract_urbanization_data[tract_id].copy()
            new_tract_data = {}
            for population_type in pop_types:
                new_tract_data[population_type+" Pop."] = tract_data[population_type]*population
            for population_type in list(new_tract_data.keys()):
                cd_urbanization_data[tract_cd][population_type] += new_tract_data[population_type]
    except KeyError:
        pass
# convert data to csv
columns = ["District Code", "State", "Seat"]
for district in cd_urbanization_data:
    district_name = district
    district = cd_urbanization_data[district_name]
    district["District Code"] = district_name
    district["State"] = code_to_state[district_name]
    district["Seat"] = code_to_seat[district_name]
    population = 0
    total_percent = 0
    for population_type in pop_types:
        pop_type_data = district[population_type+" Pop."]
        population += pop_type_data
    district["Total Pop."] = population
    for population_type in pop_types:
        pop_type_data = district[population_type+" Pop."]
        district[population_type+" Pop. %"] = pop_type_data/population
    district["Total Pop. %"] = population/population
for population_type in pop_types:
    columns.append(population_type+" Pop.")
columns.append("Total Pop.")
for population_type in pop_types:
    columns.append(population_type+" Pop. %")
columns.append("Total Pop. %")
dataframe_ready_data = {}
for cd in cd_urbanization_data:
    district = cd_urbanization_data[cd]
    dataframe_ready_data[cd] = {}
    for column in columns:
        dataframe_ready_data[cd][column] = district[column]
urbanization_dataframe = pd.DataFrame(dataframe_ready_data).T
urbanization_dataframe.set_index('District Code', inplace=True)
urbanization_dataframe.to_csv("../urbanization_data_118th_congress.csv")  # save to CSV - everything's completed now
print("Urbanization calculations complete; saved to urbanization_data_118th_congress.csv")
