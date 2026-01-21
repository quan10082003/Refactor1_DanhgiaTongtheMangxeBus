
from lxml import etree
import pandas
import numpy as np
from sympy import root

class HomeCoordinate:
    def __init__(self, person_id: str, x: float, y: float):
        self.person_id = person_id
        self.x = x
        self.y = y

class StopCoordinate:
    def __init__(self, stop_id: str, x: float, y: float):
        self.stop_id = stop_id
        self.x = x
        self.y = y

def get_home_coordinate(plan_path: str) -> list[HomeCoordinate] :
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(plan_path, parser)
    root = tree.getroot()

    home_coordinates: list[HomeCoordinate] = []

    for node in root.xpath('//population/person'):
        id = node.xpath('@id')[0]
        act = node.xpath(('./plan[@selected = "yes"]/act[@type="home"]'))
        x = act[0].xpath('@x')[0]
        y = act[0].xpath('@y')[0]
        # print([id,x,y])

        home_coordinates.append(HomeCoordinate(id, float(x), float(y)))

        return home_coordinates

def get_full_stop_coordinate(schedule_path:  str) -> set[StopCoordinate]:
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(schedule_path, parser)
    root = tree.getroot()

    full_stop_coordinate : set[StopCoordinate] = set()

    for node in root.xpath('//transitSchedule/transitStops/stopFacility'):
        id = node.xpath("@id")[0]
        x = node.xpath("@x")[0]
        y = node.xpath("@y")[0]
        # print([id,x,y])
        full_stop_coordinate.add(StopCoordinate(id, float(x), float(y)))

    return full_stop_coordinate

    

def get_bus_stop_coordinate(schedule_path:  str, home:  set[StopCoordinate] ) -> set[StopCoordinate]:
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(schedule_path, parser)
    root = tree.getroot()

    full_stop_coordinate : set[StopCoordinate] = set()
    bus_stop_coordinate : set[StopCoordinate] = set()
    hint_bus_route = "pt"

    for node in root.xpath('//transitSchedule/transitLine/transitRoute'):
        results = node.xpath('transportMode/text()')[0]
        if hint_bus_route in str(results).lower():
            stop_tag_list = node.xpath("./routeProfile/stop")
            for stop in stop_tag_list:
                stop_id = stop.xpath('@refId')[0]
                for full_stop in full_stop_coordinate:
                    if stop_id == full_stop.stop_id:
                        print([stop_id, full_stop.x, full_stop.y])
                        bus_stop_coordinate.add(full_stop)
                        break

    return bus_stop_coordinate


if __name__ == "__main__":
    home_coor = get_full_stop_coordinate("data\simple_scenario\plans.xml")
    bus_cor = get_full_stop_coordinate("src\core\plan_processor.py" )