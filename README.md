# Structure of the code

Given an address, the official number fo the municipality is identified.

<pre>
python identify_commune.py -addr "Via La Santa 1, Lugano, Ticino, Svizzera"
</pre>

Download the data from REA of the municipality where the building is located.
The m
<pre>
python download_rea_gdf.py -can TI -com 5192
</pre>

Estimate the demand (SH and DHW) for every building in the area.
<pre>
python post_process_gdf.py -com 5192
</pre>


Define a radius in meters from the address, and a maximum number of users in the network.  
Identify the users in the defined area.  
Create the topology of the network.  
Plot the results.  
Print the main KPIs.  
<pre>
python topology_finder.py -addr "Via La Santa 1, Lugano, Svizzera" -r 100 -n 10
</pre>



# Future developments

1. Automatize the procedure
2. Analyze different scenarios and find the optimum












