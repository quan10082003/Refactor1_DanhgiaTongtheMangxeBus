import pandas as pd
import numpy as np
from lxml import etree

def getTransitVehicleDict(transitVehiclePath: str) -> dict:
    
    tree = etree.parse(transitVehiclePath)
    root = tree.getroot()

    ns = {'m': 'http://www.matsim.org/files/dtd'}
    vehtype_dict = {}

    for node in root.xpath("//m:vehicleDefinitions/m:vehicle", namespaces=ns):
        id = node.xpath("@id")[0]
        type = node.xpath("@type")[0]
        vehtype_dict[id] = type

    return vehtype_dict

if __name__ == "__main__":
    transitVehiclePath = "data/real/transitVehicles.xml"
    vehtype_dict = getTransitVehicleDict(transitVehiclePath)
    print(vehtype_dict)
    print(f"Total vehicle : {len(vehtype_dict.values())}")