# Structure of the code

Given an address, the official number fo the municipality is identified.

<pre>
python identify_commune.py -addr "Via La Santa 1, Lugano, Ticino, Svizzera"
</pre>

Download the data from REA of the municipality where the building is located.
The main parameters are the location (coordinates), the age, the type, the floor area and the number of floors.
<pre>
python download_rea_gdf.py -can TI -com 5192
</pre>

Estimate the demand (SH and DHW) for every building in the area.
The demand data is taken from _Pampuri et al., Mappatura delle aree idonee alle reti di 
teleriscaldamento, 2018_  (https://www4.ti.ch/fileadmin/DT/temi/risparmio_energetico/teleriscaldamento/documenti/Rapporto_Mappatura_aree_idonee_teleriscaldamento_09032018.pdf)
<pre>
python post_process_gdf.py -com 5192
</pre>


Define a radius ***r*** in meters from the address, and a maximum number of users _**n**_ in the network. 
Identify the _**n**_ users with the highest demand in the defined area.  
Considering the address as the central plant, the topology of the network is created using existing roads.
The map of the area with the users and the network is produced, and the main KPIs are printed to screen.
 
<pre>
python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 100 -n 10
</pre>



# Future developments

1. Automatize the procedure
2. Analyze different scenarios and find the optimum












