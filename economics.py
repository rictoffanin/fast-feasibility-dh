import numpy as np
import argparse
import geopandas as gpd
import pandas as pd
from pathlib import Path


def parameters_with_calc(hs_type, q_annual, p_max, lhd):

    hs = {}
    if hs_type == 'ashp' or hs_type == 'ASHP':

        hs['k_prod'] = (lambda x: 14677 * pow(x, -0.683))(min(p_max,50))
        hs['i_prod'] = hs['k_prod'] * p_max  # CHF / kW_th
        hs['i_dis'] = 0.00 * q_annual
        hs['i_aux'] = 0.00 * q_annual
        hs['i_con'] = 0.00 * q_annual

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'wshp' or hs_type == 'WSHP':

        hs['k_prod'] = (lambda x: 16625 * pow(x, -0.321))(min(p_max,500))
        hs['i_prod'] = hs['k_prod'] * p_max  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 4.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gshp' or hs_type == 'GSHP':

        hs['k_prod'] = (lambda x: 15962 * pow(x, -0.259))(min(p_max,500))
        hs['i_prod'] = hs['k_prod'] * p_max  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.70  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gas' or hs_type == 'GAS':

        hs['k_prod'] = (lambda x: 945 * pow(x, 0.000))(p_max)
        hs['i_prod'] = (lambda x: 945 * pow(x, 0.000))(p_max) * p_max  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.87  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.093  # CHF/kWh_th

    elif hs_type == 'oil' or hs_type == 'OIL':

        hs['k_prod'] = (lambda x: 880 * pow(x, 0.000))(p_max)
        hs['i_prod'] = (lambda x: 880 * pow(x, 0.000))(p_max) * p_max  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    elif hs_type == 'htdhn' or hs_type == 'ltdhn' or hs_type == 'HTDHN' or hs_type == 'LTDHN':

        hs['k_prod'] = (lambda x: 16625 * pow(x, -0.321))(min(p_max,500))
        hs['i_prod'] = hs['k_prod'] * p_max  # CHF / kW_th
        hs['i_dis'] = dis_cost_calc(lhd, q_annual)
        hs['i_aux'] = 0.18 * q_annual  # percent of total heating demand
        hs['i_con'] = 0.03 * q_annual  # percent of total heating demand

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    hs['I_inv_tot'] = hs['i_prod'] + hs['i_dis'] + hs['i_aux'] + hs['i_con']

    hs['I_inv_yearly'] = hs['I_inv_tot'] * annuity(hs['lifetime'])
    hs['I_O&M_yearly'] = hs['k_O&M'] * hs['I_inv_tot']
    hs['I_energy_yearly'] = hs['price'] * (q_annual / hs['eta'])
    hs['I_yearly'] = hs['I_inv_yearly'] + hs['I_O&M_yearly'] + hs['I_energy_yearly']

    return hs


def lcoh_calculator(hs_type, q_annual, p_max, lhd, lt_project=40, r=0.03):

    hs = parameters_with_calc(hs_type, q_annual, p_max, lhd)
    k_a = annuity(lt_project, r)
    hs['I_inv_yearly_lt_corrected'] = hs['I_inv_tot'] * lt_project / hs['lifetime'] * k_a
    num = hs['I_inv_yearly_lt_corrected'] + hs['I_O&M_yearly'] + hs['I_energy_yearly']
    hs['LCOH'] = num / q_annual
    return hs['LCOH'], hs


def annuity(lt, r=0.03):

    num = pow(1+r, lt) * r
    den = pow(1+r, lt) - 1
    return num / den


def net_diam(lhd):
    lhd = lhd * (pow(10, 6) / 3600)  # kWh/m to GJ/m
    return 0.0486 * np.log(lhd) + 0.0007


def dis_cost_calc(lhd, q):
    c1 = 315  # CHF/m
    c2 = 2224  # CHF/m
    k_loss = 0.08
    a = annuity(40)
    d_ave = net_diam(lhd)

    return (a*(c1+c2*d_ave)) / lhd * q * (1 + k_loss)


def write_results_to_file(data, folder, name, suffix):

    fileDir = os.path.dirname(os.path.abspath(__file__)) + folder + suffix + "\\"
    Path(fileDir).mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame.from_dict(data)

    fn = fileDir + name + ".csv"
    df.to_csv(fn, sep=";", encoding='utf-8-sig')


# Main
if __name__ == "__main__":
    # python economics.py -addr "Via La Santa 1, Lugano, Svizzera" -r 1000 -n 10 -t LTDHN

    from user_finder import com_num
    import os

    print('\nProgram started\n')

    # Input args
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-addr', help='address of the generation plant')
    arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    arg_parser.add_argument('-n', help='maximum number of customers in the network', type=int)
    arg_parser.add_argument('-t', help='type: low-temperature (LTDHN) or high-temperature (HTDHN) district heating')

    args = arg_parser.parse_args()
    address = args.addr
    radius = args.r
    n_max = args.n
    net_type = args.t

    gmd, p = com_num(address)
    point = {'geometry': [p]}
    point = gpd.GeoDataFrame(point, crs='epsg:21781')

    # saving the results in a .csv file
    absFilePath = os.path.abspath(__file__)
    fileDir = os.path.dirname(os.path.abspath(__file__))
    parentDir = os.path.dirname(fileDir)

    x_coord = round(point.geometry.x.values[0], 3)
    y_coord = round(point.geometry.y.values[0], 3)

    suffix = "-%s-x%s-y%s-r%s-n%s-%s" % (gmd, x_coord, y_coord, int(radius), n_max, net_type)
    folder = "\\output\\results" + suffix + "\\"
    fn = fileDir + folder + "network-energy-kpi.csv"

    kpi = pd.read_csv(fn, sep=';')

    names = ['ashp', 'wshp', 'gshp', 'gas', 'oil', net_type]
    lcoh = {}
    par = {}
    for name in names:
        if name == 'htdhn' or 'ltdhn' or 'HTDHN' or 'LTDHN':
            a, b = lcoh_calculator(name, kpi['q_network'].values[0],
                                   kpi['p_network'].values[0], kpi['lhd_energy'].values[0])
            lcoh[name] = a
            par[name] = b
        else:
            a, b = lcoh_calculator(name, kpi['q_individual'].values[0],
                                   kpi['p_individual'].values[0], kpi['lhd_energy'].values[0])
            lcoh[name] = a
            par[name] = b

    write_results_to_file(par, "\\output\\results", "economic-kpi", suffix)


    print('\nProgram ended\n')