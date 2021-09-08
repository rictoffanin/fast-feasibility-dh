import numpy as np


def parameters(hs_type):

    hs = {}
    if hs_type == 'ashp' or 'ASHP':
        hs['i_prod'] = lambda x: 14677 * pow(x, -0.683)  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'wshp' or 'WSHP':
        hs['i_prod'] = lambda x: 16625 * pow(x, -0.321)  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 4.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gshp' or 'GSHP':
        hs['i_prod'] = lambda x: 15962 * pow(x, -0.259)  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.70  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gas' or 'GAS' or 'gas boiler':
        hs['i_prod'] = lambda x: 945 * pow(x, 0.000)  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.87  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.093  # CHF/kWh_th

    elif hs_type == 'oil' or 'OIL' or 'oil boiler':
        hs['i_prod'] = lambda x: 880 * pow(x, 0.000)  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    elif hs_type == 'high-temperature district heating' or 'low-temperature district heating' or 'htdh' or 'ltdh':
        hs['i_prod'] = lambda x: 16625 * pow(x, -0.321)  # CHF / kW_th
        hs['i_dis'] = dis_cost_calc
        hs['i_aux'] = 0.18  # percent of total heating demand
        hs['i_con'] = 0.03  # percent of total heating demand

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    return hs


def parameters_with_calc(hs_type, q, p, lhd):

    hs = {}
    if hs_type == 'ashp' or 'ASHP':
        hs['i_prod'] = (lambda x: 14677 * pow(x, -0.683))(p) * p  # CHF / kW_th
        hs['i_dis'] = 0.00 * q
        hs['i_aux'] = 0.00 * q
        hs['i_con'] = 0.00 * q

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'wshp' or 'WSHP':
        hs['i_prod'] = (lambda x: 16625 * pow(x, -0.321))(p) * p  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 4.00  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gshp' or 'GSHP':
        hs['i_prod'] = (lambda x: 15962 * pow(x, -0.259))(p) * p  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.27
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.01  # % of total investment cost

        hs['eta'] = 3.70  # efficiency [-]
        hs['lifetime'] = 25  # years
        hs['price'] = 0.201  # CHF/kWh_th

    elif hs_type == 'gas' or 'GAS' or 'gas boiler':
        hs['i_prod'] = (lambda x: 945 * pow(x, 0.000))(p) * p  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.87  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.093  # CHF/kWh_th

    elif hs_type == 'oil' or 'OIL' or 'oil boiler':
        hs['i_prod'] = (lambda x: 880 * pow(x, 0.000))(p) * p  # CHF / kW_th
        hs['i_dis'] = 0.00
        hs['i_aux'] = 0.00
        hs['i_con'] = 0.00

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    elif hs_type == 'high-temperature district heating' or 'low-temperature district heating' or 'htdh' or 'ltdh':
        hs['i_prod'] = (lambda x: 16625 * pow(x, -0.321))(p) * p  # CHF / kW_th
        hs['i_dis'] = dis_cost_calc(lhd, q)
        hs['i_aux'] = 0.18  # percent of total heating demand
        hs['i_con'] = 0.03  # percent of total heating demand

        hs['share_equip'] = 0.37
        hs['share_inst'] = 1.00 - hs['share_equip']

        hs['k_O&M'] = 0.025  # % of total investment cost

        hs['eta'] = 0.83  # efficiency [-]
        hs['lifetime'] = 20  # years
        hs['price'] = 0.078  # CHF/kWh_th

    hs['I_inv_tot'] = hs['i_prod'] + hs['i_dis'] + hs['i_aux'] + hs['i_con']

    hs['I_inv_yearly'] = hs['I_inv_tot'] * annuity(hs['lifetime'])
    hs['I_O&M_yearly'] = hs['k_O&M'] * hs['I_inv_tot']
    hs['I_energy_yearly'] = hs['price'] * (q / hs['eta'])
    hs['I_yearly'] = hs['I_inv_yearly'] + hs['I_O&M_yearly'] + hs['I_energy_yearly']

    return hs


def lcoh_calculator(hs_type, q, p, lhd, lt_project=40, r=0.03):

    hs = parameters_with_calc(hs_type, q, p, lhd)
    a = annuity(lt_project, r)
    hs['I_inv_yearly_lt_corrected'] = hs['I_inv_tot']*lt_project/hs['lifetime'] * a
    num = hs['I_inv_yearly_lt_corrected'] + hs['I_O&M_yearly'] + hs['I_energy_yearly']

    return num / q, hs


def economic_calc(cluster, lhd):

    p_individual = cluster.loc[0, 'P_tot']
    q_individual = cluster.loc[0, 'fab_tot']
    p_network = cluster['P_tot'].sum()  # todo: add concurrency factor
    q_network = cluster['fab_tot'].sum()

    i_dis = dis_cost_calc(lhd, q_network)
    # i_prod = c_inv_wshp(p_network) * p_network * 2
    i_aux = 0.18 * q_network
    i_con = 0.03 * q_network
    # i_dhn = i_prod + i_dis + i_aux + i_con
    k_OandM_dhn = 0.04
    eta_dhn = 4.00
    lt_dhn = 40
    # p_dhn = p_ashp * 0.8

    c_inv_oil = 945  # CHF/kW_th
    k_inst_oil = 0.270  # 27% of the total investment cost
    k_equip_oil = 1 - k_inst_oil  # 73% of the total investment cost
    k_OandM_oil = 0.025  # 2.5% of total investment cost per year
    eta_oil = 0.83
    lt_oil = 20  # lifetime of the gas boiler
    p_oil = 0.078  # CHF/kWh

    print("\nLCOH for individual oil boiler")
    lcoh_calc(c_inv_oil*p_individual, k_OandM_oil, p_oil, eta_oil, q_individual, lt_oil)

    c_inv_gas = 945  # CHF/kW_th
    k_inst_gas = 0.270  # 27% of the total investment cost
    k_equip_gas = 1 - k_inst_gas  # 73% of the total investment cost
    k_OandM_gas = 0.025  # 2.5% of total investment cost per year
    eta_gas = 0.87
    lt_gas = 20  # lifetime of the gas boiler
    p_gas = 0.087

    print("\nLCOH for individual gas boiler")
    lcoh_calc(c_inv_gas*p_individual, k_OandM_gas, p_gas, eta_gas, q_individual, lt_gas)

    c_inv_ashp = lambda x: 14677 * pow(x, -0.683)
    p_max_ashp = 50  # kW
    k_inst_ashp = 0.270
    k_equip_ashp = 1 - k_inst_ashp
    k_OandM_ashp = 0.01  # 1% of the total investment cost per year
    eta_ashp = 3.00
    p_ashp = 0.201
    lt_ashp = 25  # years

    p_inv = max(p_individual, p_max_ashp)
    print("\nLCOH for ASHP")
    lcoh_calc(c_inv_ashp(p_inv) * p_individual, k_OandM_ashp, p_ashp, eta_ashp, q_individual, lt_ashp)

    c_inv_gshp = lambda x: 15962 * pow(x, -0.259)
    p_max_gshp = 500  # kW
    k_inst_gshp = 0.270
    k_equip_gshp = 1 - k_inst_ashp
    k_OandM_gshp = 0.01  # 1% of the total investment cost per year
    eta_gshp = 3.70
    lt_gshp = 25  # years
    p_gshp = p_ashp

    print("\nLCOH for GSHP")
    lcoh_calc(c_inv_gshp(p_individual) * p_individual, k_OandM_gshp, p_gshp, eta_gshp, q_individual, lt_gshp)

    c_inv_wshp = lambda x: 16625 * pow(x, -0.321)
    p_max_wshp = 500  # kW
    k_inst_wshp = 0.270
    k_equip_wshp = 1 - k_inst_ashp
    k_OandM_wshp = 0.01  # 1% of the total investment cost per year
    eta_wshp = 4.00
    lt_wshp = 25  # years
    p_wshp = p_ashp

    print("\nLCOH for WSHP")
    lcoh_calc(c_inv_wshp(p_individual) * p_individual, k_OandM_wshp, p_wshp, eta_wshp, q_individual, lt_wshp)

    i_dis = dis_cost_calc(lhd, q_network)
    i_prod = c_inv_wshp(p_network) * p_network * 2
    i_aux = 0.18*q_network
    i_con = 0.03*q_network
    i_dhn = i_prod + i_dis + i_aux + i_con
    k_OandM_dhn = 0.04
    eta_dhn = 4.00
    lt_dhn = 40
    p_dhn = p_ashp*0.8

    print("\nLCOH for DHN")
    lcoh_calc(i_dhn, k_OandM_dhn, p_dhn, eta_dhn, q_network, lt_dhn)


def lcoh_calc(inv, k_OandM, p_e, eta, q, lt, r=0.03):

    a = annuity(lt, r)
    e = q*p_e / eta
    lcoh = (a*inv + inv*k_OandM + e) / q
    print("The LCOH is", "{:.3f}".format(lcoh), "CHF/kWh")
    return lcoh


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


# Main
if __name__ == "__main__":
    # python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 1000 -n 10

    # from user_finder import com_num, clusterize
    # from economics import economic_calc, parameters_with_calc, lcoh_calculator
    #
    # print('\nProgram started\n')
    #
    # # Input args
    # arg_parser = argparse.ArgumentParser()
    # arg_parser.add_argument('-addr', help='address of the generation plant')
    # arg_parser.add_argument('-r', help='radius in meters around the generation plant', type=float)
    # arg_parser.add_argument('-n', help='maximum number of customers in the network', type=int)
    #
    # args = arg_parser.parse_args()
    # address = args.addr
    # radius = args.r
    # n_max = args.n
    #
    # gmd, p = com_num(address)
    # fileDir = os.path.dirname(os.path.abspath(__file__))
    # fp = fileDir + "\\output\\processed_data\\data-" + str(gmd) + ".csv"
    #
    # temp = pd.read_csv(fp, sep=";", index_col='index')
    # temp['geometry'] = temp['geometry'].apply(wkt.loads)
    # b = gpd.GeoDataFrame(temp, crs='epsg:21781')
    # # print(b.head())
    #
    # # type = "HTDHN"
    # # clusterize(b, gmd, radius, p, n_max, type)
    # #
    # # fn = "cluster-%s-%s.geojson" % (gmd, type)
    # # c, lhd = network_finder(fn, address, radius)
    # # economic_calc(c, lhd)  # todo: to be removed
    # #
    # # type = "LTDHN"
    # # clusterize(b, gmd, radius, p, n_max, type)
    #
    # fn = "cluster-%s-%s.geojson" % (gmd, type)
    # c, lhd = network_finder(fn, address, radius)
    #
    # # todo: to be added to the economics main
    # p_individual = c.loc[0, 'P_tot']
    # q_individual = c.loc[0, 'fab_tot']
    # p_network = c['P_tot'].sum()  # todo: add concurrency factor
    # q_network = c['fab_tot'].sum()
    #
    # # economic_calc(c, lhd)
    #
    # # par = parameters_with_calc(type, q_network, p_network, lhd)
    # lcoh, par = lcoh_calculator(type, q_network, p_network, lhd)
    # print("The LCOH for", type, "is", "{:.3f}".format(lcoh), "CHF/kWh")
    # df = pd.DataFrame([par])
    # print(df)

    print('\nProgram ended\n')
