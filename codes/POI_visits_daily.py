# encoding: utf-8
# copyright: GeoDS Lab, University of Wisconsin-Madison
# authors: Yuhao Kang, Song Gao, Jinmeng Rao
import pandas as pd
import numpy as np
import os
import geopandas as gpd
import argparse
import datetime

parser = argparse.ArgumentParser(description='Month, start day, end day')
parser.add_argument('--month', type=str, help='Month')
parser.add_argument('--day', type=int, help='Day')

args = parser.parse_args()

month = args.month
day = args.day
day_str = str(day).zfill(2)


# Read shp
cbgs_shp = gpd.read_file('cbg_us.shp')
ct_shp = gpd.read_file('ct_us.shp')
county_shp = gpd.read_file('county_us.shp')
state_shp = gpd.read_file('state_us.shp')


# Pop
pop_ct = pd.read_csv('../resources/pop_ct.csv', dtype={"ct":"object"})
pop_county = pd.read_csv('../resources/pop_county.csv', dtype={"county":"object"})
pop_state = pd.read_csv('../resources/pop_state.csv', dtype={"state":"object"})


# Iterate visit flows
cbg_visits = pd.read_csv(f'{month}/{day_str}/2020-{month}-{day_str}-social-distancing.csv.gz')
flows_unit = []

for i, row in enumerate(cbg_visits.itertuples()):
    if row.destination_cbgs == "{}":
        continue
    else:
        origin = row.origin_census_block_group
        destination = eval(row.destination_cbgs)
        for key, value in destination.items():
            d = str(key).zfill(12)
            v = value
            o = str(origin).zfill(12)
            flows_unit.append([o, d, v])
cbg_visits_flow_all = pd.DataFrame(flows_unit, columns=["cbg_o", "cbg_d", "visitor_flows"])

cbg_visits_flow_all_geo = pd.merge(left=cbg_visits_flow_all, right=cbgs_shp[["cbg", "ct", "county_fip", "StateFIPS"]], 
                                   left_on="cbg_o", right_on="cbg")
cbg_visits_flow_all_geo = pd.merge(left=cbg_visits_flow_all_geo, right=cbgs_shp[["cbg", "ct", "county_fip", "StateFIPS"]], 
                                   left_on="cbg_d", right_on="cbg", suffixes=["__o", "__d"])
cbg_visits_flow_all_geo = cbg_visits_flow_all_geo.drop(["cbg__o", "cbg__d"], axis=1)
cbg_visits_flow_all_geo = cbg_visits_flow_all_geo.rename({"ct__o": "ct_o", "ct__d": "ct_d",
                                                          "StateFIPS__o": "state_o", "StateFIPS__d": "state_d", 
                                                         "county_fip__o":"county_o", "county_fip__d":"county_d"}, axis=1)

# Export O-D flows
def export_od(cbg_visits_flow_all_geo, scale, od_shp):
    if scale == "ct":
        scale_field = scale
    elif scale == "county":
        scale_field = f"county_fip"
    else:
        scale_field = "StateFIPS"
        
    od = cbg_visits_flow_all_geo.groupby([f"{scale}_o", f"{scale}_d"]).sum().reset_index()
    
    od_shp["lng"] = od_shp["geometry"].centroid.x
    od_shp["lat"] = od_shp["geometry"].centroid.y
    
    od_all = pd.merge(left=od, left_on=[f"{scale}_o"], 
                      right=od_shp[[f"{scale_field}", "lng", "lat"]], right_on=[f"{scale_field}"])
    od_all = pd.merge(left=od_all, left_on=[f"{scale}_d"], 
                      right=od_shp[[f"{scale_field}", "lng", "lat"]], right_on=[f"{scale_field}"],
                     suffixes=["__o", "__d"])
    
    od_all = od_all.drop([f"{scale_field}__o", f"{scale_field}__d"], axis=1)
    od_all = od_all.rename({"lng__o": "lng_o", "lat__o": "lat_o", "lng__d":"lng_d", "lat__d":"lat_d"}, axis=1)
    return od_all

ct2ct_all = export_od(cbg_visits_flow_all_geo, "ct", ct_shp)
county2county_all = export_od(cbg_visits_flow_all_geo, "county", county_shp)
state2state_all = export_od(cbg_visits_flow_all_geo, "state", state_shp)


# Num_devices
num_devices = cbg_visits[["origin_census_block_group", "device_count"]].copy()
num_devices["ct"] = num_devices["origin_census_block_group"].apply(lambda x: str(x).zfill(12)[:-1])
num_devices["county"] = num_devices["origin_census_block_group"].apply(lambda x: str(x).zfill(12)[:5])
num_devices["state"] = num_devices["origin_census_block_group"].apply(lambda x: str(x).zfill(12)[:2])
num_devices_ct = num_devices.groupby(["ct"]).sum().drop(["origin_census_block_group"], axis=1).reset_index()
num_devices_county = num_devices.groupby(["county"]).sum().drop(["origin_census_block_group"], axis=1).reset_index()
num_devices_state = num_devices.groupby(["state"]).sum().drop(["origin_census_block_group"], axis=1).reset_index()


# Pop device
pop_device_ct = pd.merge(left=num_devices_ct, left_on="ct", right=pop_ct, right_on="ct")
pop_device_ct["ratio"] = pop_device_ct["device_count"] / pop_device_ct["pop"]
pop_device_county = pd.merge(left=num_devices_county, left_on="county", right=pop_county, right_on="county")
pop_device_county["ratio"] = pop_device_county["device_count"] / pop_device_county["pop"]
pop_device_state = pd.merge(left=num_devices_state, left_on="state", right=pop_state, right_on="state")
pop_device_state["ratio"] = pop_device_state["device_count"] / pop_device_state["pop"]


# Split ct2ct data
def split_ct2ct(df, month, day_str):
    if os.path.exists(f'COVID19USFlows/daily_flows/ct2ct/{month}_{day_str}'):
        pass
    else:
        os.mkdir(f'COVID19USFlows/daily_flows/ct2ct/{month}_{day_str}')
    
    split_file = 20
    interval = int(df.shape[0]/split_file)
    for i in range(split_file):
        if i == 19:
            df_temp = df.iloc[i*interval:]
        else:
            df_temp = df.iloc[i*interval:(i+1)*interval]
        df_temp.to_csv(f'COVID19USFlows/daily_flows/ct2ct/{month}_{day_str}/daily_ct2ct_{month}_{day_str}_{i}.csv', index=False)
        
# Export O-D data with pop
def export_od_pop(od_all, scale, pop, month, day_str):
    od_pop = pd.merge(left=od_all, left_on=f"{scale}_o", right=pop, right_on=f"{scale}")
    od_pop["date"] = f"2020-{month}-{day_str}"
    od_pop["v"] = od_pop["visitor_flows"]
    od_pop = od_pop.drop(["visitor_flows", f"{scale}", "device_count", "pop"], axis=1) 
    od_pop = od_pop.rename({'v': "visitor_flows", f"{scale}_o": "geoid_o", f"{scale}_d": "geoid_d"}, axis=1)
    od_pop["pop_flows"] = od_pop.apply(lambda x: np.floor(x.visitor_flows/x.ratio), axis=1)
    od_pop = od_pop.drop(["ratio"], axis=1) 
    return od_pop

# Ct2ct output
ct2ct_pop = export_od_pop(ct2ct_all, "ct", pop_device_ct, month, day_str)
split_ct2ct(ct2ct_pop, month, day_str)

# County2county output
county2county_pop = export_od_pop(county2county_all, "county", pop_device_county, month, day_str)
county2county_pop.to_csv(f'COVID19USFlows/daily_flows/county2county/daily_county2county_{month}_{day_str}.csv', index=False)


# State2state output
state_pop = export_od_pop(state2state_all, "state", pop_device_state, month, day_str)
state_pop.to_csv(f'COVID19USFlows/daily_flows/state2state/daily_state2state_{month}_{day_str}.csv', index=False)