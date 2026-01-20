import os
import random

# --- CẤU HÌNH ---
OUTPUT_FOLDER = "data/simple_scenario"
NUM_NODES_X = 6
NUM_NODES_Y = 5

# --- THAY ĐỔI QUAN TRỌNG TẠI ĐÂY ---
# Tăng từ 500m -> 3000m (3km). 
# Đi bộ 1 cạnh mất ~40 phút -> Dân sẽ chán đi bộ ngay.
LINK_LENGTH = 3000.0 

NUM_PERSONS = 500
COORD_OFFSET_X = 460000.0 
COORD_OFFSET_Y = 5740000.0

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# ==========================================
# 1. TẠO NETWORK (HEADER V1)
# ==========================================
print("1. Đang tạo Network (Scale to)...")
nodes = []
links = []
link_id_counter = 1

for y in range(NUM_NODES_Y):
    for x in range(NUM_NODES_X):
        node_id = f"n_{x}_{y}"
        coord_x = COORD_OFFSET_X + (x * LINK_LENGTH)
        coord_y = COORD_OFFSET_Y + (y * LINK_LENGTH)
        nodes.append({"id": node_id, "x": coord_x, "y": coord_y})

def add_link(from_n, to_n, modes):
    global link_id_counter
    l_id = str(link_id_counter)
    links.append({
        "id": l_id, "from": from_n, "to": to_n,
        "len": LINK_LENGTH, "modes": modes
    })
    link_id_counter += 1
    return l_id

grid_links = {} 

for y in range(NUM_NODES_Y):
    for x in range(NUM_NODES_X):
        curr = f"n_{x}_{y}"
        if x < NUM_NODES_X - 1:
            next_n = f"n_{x+1}_{y}"
            l1 = add_link(curr, next_n, "car,bus,tram,train")
            l2 = add_link(next_n, curr, "car,bus,tram,train")
            grid_links[(x, y, x+1, y)] = l1
            grid_links[(x+1, y, x, y)] = l2
        if y < NUM_NODES_Y - 1:
            next_n = f"n_{x}_{y+1}"
            l1 = add_link(curr, next_n, "car,bus,tram,train")
            l2 = add_link(next_n, curr, "car,bus,tram,train")
            grid_links[(x, y, x, y+1)] = l1
            grid_links[(x, y+1, x, y)] = l2

# COPY HEADER TU FILE network.xml CUA EM
with open(f"{OUTPUT_FOLDER}/network.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v1.dtd">\n')
    f.write('<network>\n')
    f.write('  <nodes>\n')
    for n in nodes:
        f.write(f'    <node id="{n["id"]}" x="{n["x"]}" y="{n["y"]}" />\n')
    f.write('  </nodes>\n  <links>\n')
    for l in links:
        # Tăng tốc độ freespeed lên 22.2 m/s (~80km/h) để đường thoáng, xe chạy nhanh
        f.write(f'    <link id="{l["id"]}" from="{l["from"]}" to="{l["to"]}" length="{l["len"]}" freespeed="22.2" capacity="2000.0" permlanes="1.0" modes="{l["modes"]}" />\n')
    f.write('  </links>\n</network>\n')


# ==========================================
# 2. CHUẨN BỊ DATA TUYẾN
# ==========================================
lines_def = [
    ("Bus_Line_1", "bus",   [(0,0), (1,0), (2,0), (3,0), (4,0), (5,0)]), 
    ("Bus_Line_2", "bus",   [(0,2), (1,2), (2,2), (3,2), (4,2), (5,2)]), 
    ("Bus_Line_3", "bus",   [(0,4), (1,4), (2,4), (3,4), (4,4), (5,4)]), 
    ("Tram_Line_1", "tram", [(1,0), (1,1), (1,2), (1,3), (1,4)]),        
    ("Train_Line_1", "train", [(4,0), (4,1), (4,2), (4,3), (4,4)])       
]

# ==========================================
# 3. TẠO VEHICLES & SCHEDULE
# ==========================================
print("2. Đang tạo Transit Schedule & Vehicles...")
veh_file_content = []
sched_lines = []
stop_facilities = []
used_stops = set()

# HEADER Y HỆT FILE transitVehicles.xml CỦA EM
veh_file_content.append('<?xml version="1.0" encoding="UTF-8"?>')
veh_file_content.append('<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/vehicleDefinitions_v1.0.xsd">')

# VIẾT THẲNG <vehicleType> RA NHƯ FILE CỦA EM
for vtype in ["bus", "tram", "train"]:
    cap = 100 if vtype == "train" else 50
    # Tăng tốc độ xe Bus lên (maxVelocity) nếu cần, nhưng mặc định nó sẽ theo freespeed của link
    veh_file_content.append(f'  <vehicleType id="{vtype}_type"> <capacity><seats persons="{cap}"/><standingRoom persons="0"/></capacity> <length meter="10.0"/> </vehicleType>')

# Logic tạo Tuyến
for line_name, mode, coords in lines_def:
    sched_lines.append(f' <transitLine id="{line_name}">')
    directions = [("dir_fwd", coords), ("dir_bwd", list(reversed(coords)))]
    
    for dir_id, path_coords in directions:
        route_links = []
        route_stops = []
        
        for i in range(len(path_coords) - 1):
            p1 = path_coords[i]
            p2 = path_coords[i+1]
            l_id = grid_links.get((p1[0], p1[1], p2[0], p2[1]))
            if not l_id: continue
            
            route_links.append(l_id)
            
            stop_id = f"stop_{l_id}"
            if stop_id not in used_stops:
                stop_x = COORD_OFFSET_X + p2[0]*LINK_LENGTH
                stop_y = COORD_OFFSET_Y + p2[1]*LINK_LENGTH
                stop_facilities.append(f'  <stopFacility id="{stop_id}" x="{stop_x}" y="{stop_y}" linkRefId="{l_id}"/>')
                used_stops.add(stop_id)
            
            route_stops.append(f'    <stop refId="{stop_id}" departureOffset="00:00:00" arrivalOffset="00:00:00" awaitDeparture="false"/>')

        sched_lines.append(f'  <transitRoute id="{dir_id}">')
        sched_lines.append(f'   <transportMode>{mode}</transportMode>')
        
        sched_lines.append('   <routeProfile>')
        for rs in route_stops: sched_lines.append(rs)
        sched_lines.append('   </routeProfile>')
        
        # SCHEDULE V1: Dùng thẻ <link refId>
        sched_lines.append('   <route>')
        for link_ref in route_links:
            sched_lines.append(f'    <link refId="{link_ref}"/>')
        sched_lines.append('   </route>')
        
        sched_lines.append('   <departures>')
        start_time = 6 * 3600 
        for dep_i in range(5): 
            dep_time = start_time + (dep_i * 3600) 
            h = int(dep_time // 3600)
            m = int((dep_time % 3600) // 60)
            s = int(dep_time % 60)
            time_str = f"{h:02}:{m:02}:{s:02}"
            
            veh_id = f"veh_{line_name}_{dir_id}_{dep_i}"
            sched_lines.append(f'    <departure id="{veh_id}" departureTime="{time_str}" vehicleRefId="{veh_id}"/>')
            
            # XE CỤ THỂ
            veh_file_content.append(f' <vehicle id="{veh_id}" type="{mode}_type"/>')
            
        sched_lines.append('   </departures>')
        sched_lines.append('  </transitRoute>')
    sched_lines.append(' </transitLine>')

# Đóng thẻ vehicleDefinitions
veh_file_content.append('</vehicleDefinitions>')
with open(f"{OUTPUT_FOLDER}/transitVehicles.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(veh_file_content))

# HEADER Y HỆT FILE schedule.xml CỦA EM
with open(f"{OUTPUT_FOLDER}/schedule.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v1.dtd">\n')
    f.write('<transitSchedule>\n')
    f.write(' <transitStops>\n')
    for sf in stop_facilities: f.write(sf + "\n")
    f.write(' </transitStops>\n')
    for line in sched_lines: f.write(line + "\n")
    f.write('</transitSchedule>\n')


# ==========================================
# 4. TẠO PLANS (HEADER V5 - CHUẨN COTTBUS)
# ==========================================
print("3. Đang tạo Plans...")
with open(f"{OUTPUT_FOLDER}/plans.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
    f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v5.dtd">\n')
    f.write('<population>\n')
    
    min_x, max_x = COORD_OFFSET_X, COORD_OFFSET_X + (NUM_NODES_X-1)*LINK_LENGTH
    min_y, max_y = COORD_OFFSET_Y, COORD_OFFSET_Y + (NUM_NODES_Y-1)*LINK_LENGTH
    
    for p_i in range(NUM_PERSONS):
        hx = random.uniform(min_x, max_x)
        hy = random.uniform(min_y, max_y)
        wx = random.uniform(min_x, max_x)
        wy = random.uniform(min_y, max_y)
        
        f.write(f' <person id="p_{p_i}">\n')
        f.write(f'  <plan selected="yes">\n')
        f.write(f'   <act type="home" x="{hx}" y="{hy}" end_time="07:00:00" />\n')
        f.write('   <leg mode="pt"/>\n') 
        f.write(f'   <act type="work" x="{wx}" y="{wy}" end_time="17:00:00" />\n')
        f.write('   <leg mode="pt"/>\n')
        f.write(f'   <act type="home" x="{hx}" y="{hy}" />\n')
        f.write('  </plan>\n')
        f.write(' </person>\n')
        
    f.write('</population>\n')


# ==========================================
# 5. TẠO CONFIG (2 VÒNG, BẬT ĐỒ THỊ, BÊ NGUYÊN COTTBUS VÀO)
# ==========================================
print("4. Đang tạo Config...")
config_content = f"""<?xml version="1.0" ?>
<!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
<config>
    <module name="global">
        <param name="coordinateSystem" value="Atlantean" />
    </module>

    <module name="controler">
        <param name="outputDirectory" value="output" />
        <param name="firstIteration" value="0" />
        
        <param name="lastIteration" value="2" />
        
        <param name="eventsFileFormat" value="xml" />
        <param name="createGraphs" value="true" />
        
        <param name="overwriteFiles" value="deleteDirectoryIfExists" />
        <param name="mobsim" value="qsim" />
    </module>
    
    <module name="plans" >
        <param name="inputPlansFile" value="plans.xml" />
    </module>
    <module name="network" >
        <param name="inputNetworkFile" value="network.xml" />
    </module>
    
    <module name="qsim">
        <param name="startTime" value="00:00:00"/>
        <param name="endTime" value="30:00:00"/>
        <param name="flowCapacityFactor" value="0.25"/>
        <param name="storageCapacityFactor" value="0.25"/>
    </module>
    
    <module name="scoring">
        <parameterset type="scoringParameters">
            <param name="lateArrival" value="-18.0" />
            <param name="earlyDeparture" value="-0.0" />
            <param name="performing" value="+6.0" />
            <param name="waiting" value="-0.0" />
            <param name="waitingPt" value="-0.1" />

            <parameterset type="activityParams">
                <param name="activityType" value="home" />
                <param name="typicalDuration" value="12:00:00" />
            </parameterset>
            <parameterset type="activityParams">
                <param name="activityType" value="work" />
                <param name="typicalDuration" value="08:00:00" />
            </parameterset>
            <parameterset type="activityParams">
                <param name="activityType" value="pt interaction" />
                <param name="scoringThisActivityAtAll" value="false" />
                <param name="typicalDuration" value="00:02:00" />
            </parameterset>

            <parameterset type="modeParams">
                <param name="mode" value="car" />
                <param name="constant" value="-5.0" />
                <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
                <param name="monetaryDistanceRate" value="-0.0002" />
            </parameterset>
            
            <parameterset type="modeParams">
                <param name="mode" value="pt" />
                <param name="constant" value="5.0" />
                <param name="marginalUtilityOfTraveling_util_hr" value="-1.0" />
                <param name="monetaryDistanceRate" value="0.0" />
            </parameterset>
            
            <parameterset type="modeParams">
                <param name="mode" value="walk" />
                <param name="constant" value="0.0" />
                <param name="marginalUtilityOfTraveling_util_hr" value="-12.0" />
            </parameterset>
            
            <parameterset type="modeParams">
                <param name="mode" value="bike" />
                <param name="constant" value="-2.0" />
                <param name="marginalUtilityOfTraveling_util_hr" value="-6.0" />
            </parameterset>
        </parameterset>
    </module>

    <module name="replanning">
        <param name="fractionOfIterationsToDisableInnovation" value="0.8" />
        <param name="maxAgentPlanMemorySize" value="5" />
        <parameterset type="strategysettings" >
            <param name="strategyName" value="ChangeExpBeta" />
            <param name="weight" value="0.7" />
        </parameterset>
        <parameterset type="strategysettings">
            <param name="strategyName" value="ChangeTripMode" />
            <param name="weight" value="0.3" /> 
        </parameterset>
    </module>
    
    <module name="transit">
        <param name="transitScheduleFile" value="schedule.xml" />
        <param name="vehiclesFile" value="transitVehicles.xml" />
        <param name="transitModes" value="pt" />
        <param name="useTransit" value="true" />
    </module>
    
    <module name="transitRouter">
        <param name="searchRadius" value="3000" />
        <param name="extensionRadius" value="1000" />
        <param name="maxBeelineWalkConnectionDistance" value="1000" />
    </module>

    <module name="changeMode">
        <param name="modes" value="car,pt" />
    </module>
</config>
"""
with open(f"{OUTPUT_FOLDER}/config.xml", "w", encoding="utf-8") as f:
    f.write(config_content)

print(f"XONG! Đã scale bản đồ lên 3km/link để ép dân đi PT: {OUTPUT_FOLDER}")