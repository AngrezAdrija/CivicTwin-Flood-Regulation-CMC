# pyrefly: ignore [missing-import]
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import json
import os

def humanize_docx():
    src_file = 'FinalReport_25MCA0212.docx'
    print(f"Loading {src_file}...")
    doc = docx.Document(src_file)

    # Dictionary of paragraph replacements
    # Format: paragraph_index -> replacement_info
    # For normal paragraphs: {'type': 'normal', 'text': '...'}
    # For bullet paragraphs: {'type': 'bullet', 'bullet': '•  ', 'label': 'Bold Label: ', 'text': '...'}
    
    replacements = {
        # Frontmatter: Acknowledgement
        139: {
            'type': 'normal',
            'text': (
                "I would like to express my sincere gratitude to my Dissertation-1 guide, Dr. Parimala M., "
                "Professor Grade I, School of Computer Science Engineering and Information Systems (SCORE), "
                "Vellore Institute of Technology, Vellore. Her steady guidance, constructive critique, and deep familiarity "
                "with urban hydro-informatics and cyber-physical systems were invaluable throughout this project. She helped "
                "me look past raw algorithmic simulations and consider the practical realities of municipal infrastructure "
                "and civic governance."
            )
        },
        141: {
            'type': 'normal',
            'text': (
                "I am deeply grateful to our Honorable Chancellor Dr. G. Viswanathan for providing the advanced research "
                "facilities at VIT. My thanks also go to respected Vice Presidents Dr. Sankar Viswanathan and Dr. Sekar "
                "Viswanathan, Vice Chancellor Dr. V. S. Kanchana Bhaaskaran, Pro-Vice Chancellor Dr. Partha Sharathi Mallick, "
                "and Registrar Dr. Jayabarathi T. for their continuous institutional encouragement."
            )
        },
        143: {
            'type': 'normal',
            'text': (
                "I extend my warm thanks to Dean Dr. Daphne Lopez, School of Computer Science Engineering and Information "
                "Systems; Head of the Department Dr. Senthilkumar N; MCA Project Coordinator Dr. Krishnamoorthy N; and "
                "SCORE Project Coordinator Dr. Karthikeyan P, along with all my department professors and staff who "
                "offered valuable guidance during my course of study."
            )
        },
        145: {
            'type': 'normal',
            'text': (
                "I want to thank my parents and close friends for their unwavering patience and support while I worked "
                "on this dissertation. Finally, I appreciate everyone who offered technical advice, shared data, or "
                "assisted me along the way."
            )
        },
        
        # Frontmatter: Executive Summary
        164: {
            'type': 'normal',
            'text': (
                "Every monsoon season, secondary Indian cities face the same crisis: sudden, heavy rain hits poorly maintained "
                "roadside drains, turning busy streets into stagnant pools and bringing daily life to a halt. In Vellore, Tamil Nadu, "
                "rapid construction has replaced open soil with concrete, while domestic trash, road sand, and building debris clog "
                "the city's drainage channels. Most municipal corporations manage this reactively. Desilting machinery and suction "
                "tankers are sent out only after water begins pooling on major roads or after desperate phone calls from residents. "
                "Even during pre-monsoon maintenance, supervisors typically clear whichever drain looks dirtiest on the surface. That "
                "approach misses the bigger picture: a badly clogged ditch near a hilltop only spills locally, whereas a moderately "
                "silted channel downstream can block drainage for dozens of connected streets, causing backwater floods kilometers away.\n\n"
                "This dissertation presents CivicTwin, a cyber-physical digital twin designed to give municipal administrators the "
                "predictive foresight they need before storms strike. Using geospatial and survey records from Vellore City Municipal "
                "Corporation (CMC), the platform models 13,998 drain segments as a Directed Acyclic Graph (DAG) with 22,737 gravity "
                "flow links across 60 administrative zones. CivicTwin combines the rational runoff method, an ensemble Random Forest "
                "blockage model (achieving 89.4% classification accuracy), and a bitset-accelerated reachability engine that traces "
                "upstream dependencies across the entire network in under 20 milliseconds. Instead of prioritizing drains by local silt "
                "levels alone, CivicTwin introduces a cascade-aware dispatch algorithm that targets systemic bottlenecks—channels whose "
                "clearance restores drainage for hundreds of upstream tributaries. Simulated across rainfall intensities from 80 to "
                "160 mm/hr, the cascade-aware method clears 3.1x to 4.4x more at-risk and backwater-affected drains than traditional "
                "municipal severity heuristics under the same equipment and labor budgets. Delivered through an interactive React and "
                "FastAPI command dashboard, CivicTwin provides municipal engineers with real-time bottleneck detection, helping public "
                "works teams shift from emergency fire-fighting to proactive urban resilience."
            )
        },

        # Chapter 1: Introduction
        178: {
            'type': 'normal',
            'text': (
                "Stormwater drainage networks form the unseen backbone of any city's flood defenses. Their main job is straightforward: "
                "catch runoff during heavy rain and carry it safely to local waterways before streets turn into canals. In fast-growing "
                "secondary cities across India, such as Vellore in Tamil Nadu, this infrastructure simply cannot keep up with runaway paving "
                "and building construction. Over the past three decades, asphalt roads, paved shopfronts, and dense concrete residential "
                "layouts have blanketed natural ground that once soaked up rainwater. Consequently, urban runoff coefficients have shot up "
                "from historic estimates of 0.20–0.30 to well over 0.75–0.85, so almost all falling rain turns into instant surface runoff."
            )
        },
        179: {
            'type': 'normal',
            'text': (
                "Changing monsoon patterns have made things worse. Instead of steady rains spread over several days, showers frequently "
                "arrive as sudden, violent cloudbursts dumping 80 to 120 mm/hr in under an hour. When downpours like this strike roadside "
                "channels filled with unsegregated domestic trash, plastic bags, and eroded construction silt, the channels choke immediately. "
                "Water spills over road curbs, tears up asphalt pavements, stalls traffic, and leaves behind stagnant pools that breed "
                "dengue-carrying mosquitoes."
            )
        },
        180: {
            'type': 'normal',
            'text': (
                "Vellore City Municipal Corporation (CMC), spanning 60 municipal wards, faces this struggle every monsoon season. "
                "The city sits on uneven terrain between the rocky granite slopes of the Eastern Ghats and the lower alluvial basin of "
                "the Palar river. Stormwater rushes down hillside roads and accumulates rapidly in low-lying commercial hubs like Long "
                "Bazaar, Katpadi road junction, and the areas surrounding CMC Hospital. The city's drainage network is a patchwork of "
                "open roadside gutters, stone-masonry channels covered by footpaths, and underground pipe culverts built piece by piece "
                "over several decades. Maintaining such a sprawling, hidden network under tight municipal labor and equipment limits is a "
                "constant challenge for civic authorities."
            )
        },
        182: {
            'type': 'normal',
            'text': "Municipal flood management in most Indian urban corporations continues to operate in a reactive, ad-hoc manner:"
        },
        183: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Reactive Desilting Deployment: ',
            'text': (
                "Excavators, suction tankers, and municipal laborers are typically dispatched only after flood complaints are registered "
                "by citizens or when major transit roads are already submerged underwater."
            )
        },
        184: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Topological Blindness in Prioritization: ',
            'text': (
                "When municipal staff do carry out pre-monsoon desilting, they almost always decide which drains to clean based on how "
                "dirty a drain appears from above. This heuristic ignores the connected geometry of the network. A drain segment at a high "
                "elevation with no upstream feeder drains causes only minor, localized gutter spillage even if it is 90% clogged. On the other "
                "hand, a moderately silted conduit downstream that serves as the main outlet for forty street drains will trigger massive "
                "backwater surcharge and submerge dozens of upstream residential blocks if it chokes."
            )
        },
        185: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Absence of Predictive Hydro-Informatics Tools: ',
            'text': (
                "Public works departments lack fast, accessible software tools that combine rainfall calculations with network flow paths "
                "to flag severe failure cascades in advance. Full hydrodynamic simulation packages like US-EPA SWMM demand extensive calibration "
                "data and take hours or days to run over 14,000 conduits, making them impractical for fast operational decisions during active storms."
            )
        },
        186: {
            'type': 'normal',
            'text': (
                "Without an integrated cyber-physical twin that tracks how water moves through connected streets and pinpoints true bottlenecks, "
                "municipal teams spend scarce budgets cleaning low-impact channels while the real choke points remain clogged."
            )
        },
        188: {
            'type': 'normal',
            'text': (
                "The primary goal of this dissertation is to design, develop, and test CivicTwin, an AI-assisted cyber-physical digital twin that "
                "combines spatial graph modeling, rational hydrology, and machine learning into a real-time decision-support system for Vellore's "
                "drainage infrastructure. The project focuses on six concrete objectives:"
            )
        },
        189: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '1. Topological Graph Modeling: ',
            'text': (
                "Clean, extract, and convert the multi-modal stormwater network of Vellore Municipal Corporation from geospatial data into an "
                "elevation-directed Directed Acyclic Graph (DAG) with 22,737 directed flow links."
            )
        },
        190: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '2. Hydrologic-Hydraulic Capacity Formulation: ',
            'text': (
                "Formulate an ultra-fast, vectorized rational runoff model that calculates discharge and conduit capacity consumption across "
                "rainfall intensities between 20 and 200 mm/hr."
            )
        },
        191: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '3. Bitset Reachability Cascade Metric: ',
            'text': (
                "Implement a bitset-accelerated transitive closure algorithm that calculates the exact count of upstream tributary channels "
                "protected by each conduit (Cascade Saved) in under 20 milliseconds."
            )
        },
        192: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '4. Machine Learning Blockage Surrogate: ',
            'text': (
                "Train and evaluate an ensemble Random Forest classifier to predict conduit blockage risk and structural flood vulnerability from "
                "morphometric, spatial, and land-use variables."
            )
        },
        193: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '5. Multi-Criteria Cascade-Aware Dispatch: ',
            'text': (
                "Formulate a multi-criteria ranking algorithm that prioritizes cleaning by threat tier, upstream reachability, and capacity overload, "
                "testing it against traditional municipal heuristics across extensive simulation runs."
            )
        },
        194: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '6. Interactive Web GIS Operations Center: ',
            'text': (
                "Build a production-ready, interactive web GIS command dashboard connecting FastAPI, React-Leaflet, and PostGIS to let municipal "
                "engineers simulate storm scenarios and dispatch cleaning crews in real time."
            )
        },
        196: {
            'type': 'normal',
            'text': (
                "Urban drainage failures directly hurt city budgets, public safety, and public health. Flooded streets damage asphalt, wash "
                "away road foundations, and cause recurring potholes that cost municipal corporations crores of rupees in annual repairs. Beyond "
                "infrastructure costs, water backing up into crowded markets and residential streets creates standing pools that breed disease vectors, "
                "leading to seasonal outbreaks of dengue and chikungunya."
            )
        },
        197: {
            'type': 'normal',
            'text': (
                "Municipal budgets make the challenge even clearer. A typical civic body like CMC operates with only a handful of maintenance crews, "
                "capable of thoroughly cleaning perhaps 10 to 20 major drain segments in a single workday. In a city with almost 14,000 drain lines, "
                "guessing which drains to clean before a storm is ineffective. CivicTwin provides municipal administrators with an evidence-based roadmap "
                "that directs every cleaning crew to the highest-leverage hydraulic bottlenecks in the city."
            )
        },
        199: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Geographic Scope: ',
            'text': (
                "The study focuses strictly on the administrative limits of Vellore City Municipal Corporation (CMC), analyzing 13,998 surveyed and "
                "extracted drain conduit segments partitioned across 60 localized ward clusters."
            )
        },
        200: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Topological Scope: ',
            'text': (
                "The drainage network is modeled as a Directed Acyclic Graph containing 22,737 directed hydraulic flow edges. Conduits lacking valid GPS "
                "coordinates (37 segments out of 13,998) or located outside municipal limits are stored in the database but excluded from active dispatch ranking."
            )
        },
        201: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Hydrological Delimitations: ',
            'text': (
                "Storm runoff is estimated using the rational method calibrated via catchment basin inversion under steady-state peak intensity conditions, "
                "prioritizing sub-second operational calculations over full 2D unsteady shallow water routing."
            )
        },
        202: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Sediment and Silt Model: ',
            'text': (
                "Initial silt percentages are drawn from municipal pre-monsoon survey logs. When a conduit is cleared during simulation, its silt level "
                "resets to an empirical post-cleaning residual baseline of 5.0%."
            )
        },
        204: {
            'type': 'normal',
            'text': (
                "This dissertation is organized across nine chapters. Chapter 2 reviews prior literature in urban drainage modeling, digital twins, machine "
                "learning surrogates, and complex network cascade dynamics, highlighting existing research gaps. Chapter 3 presents system specifications, "
                "full-stack architecture, PostGIS database design, and API endpoints. Chapter 4 explains the mathematical formulations for rational hydrology, "
                "DAG construction, bitset reachability, and network risk metrics. Chapter 5 covers dataset profiling across 13,998 conduits, feature engineering, "
                "ward clustering, and the Random Forest surrogate model. Chapter 6 formalizes the dispatch optimization problem, the proposed cascade-aware "
                "strategy, and the simulation setup. Chapter 7 presents quantitative benchmark results, ward-level sensitivity analyses, and statistical "
                "significance tests across three rainfall intensities. Chapter 8 walks through the interactive web GIS operations center. Finally, Chapter 9 "
                "summarizes research contributions, practical public works recommendations, project limitations, and directions for future research."
            )
        },

        # Chapter 2: Literature Review
        208: {
            'type': 'normal',
            'text': (
                "Civil engineers have long relied on empirical and numerical formulas to design stormwater drainage. The most widely used approach for "
                "estimating peak surface runoff remains the rational method, first introduced by Kuichling in 1889 and later formalized by Chow et al. (1988):"
            )
        },
        210: {
            'type': 'normal',
            'text': (
                "Here Q is the peak runoff rate in m3/s, C is the dimensionless runoff coefficient, i represents rainfall intensity in mm/hr, and A is the "
                "tributary catchment surface area in m2. The rational method assumes that peak discharge occurs when the entire catchment contributes flow "
                "simultaneously, meaning the rainfall event lasts at least as long as the basin's time of concentration."
            )
        },
        211: {
            'type': 'normal',
            'text': "To determine flow capacity within open channels, engineers rely on Manning's equation for gravity-driven flow:"
        },
        213: {
            'type': 'normal',
            'text': (
                "In this equation, V is the mean flow velocity in m/s, n is Manning's roughness coefficient (typically 0.013–0.017 for smooth concrete and "
                "0.025–0.035 for unlined or silted earthen channels), Rh is the hydraulic radius (cross-sectional flow area divided by wetted perimeter), "
                "and S0 is the longitudinal bed slope."
            )
        },
        214: {
            'type': 'normal',
            'text': (
                "Advanced modeling packages like US-EPA SWMM solve the full one-dimensional Saint-Venant equations for unsteady open-channel flow. While SWMM "
                "provides excellent hydraulic detail, running dynamic wave simulations across thousands of interconnected links requires substantial computational "
                "time. Execution runtimes can easily stretch from several minutes to hours, and models require detailed junction invert surveys, cross-sectional "
                "measurements, and headloss calibrations. As a result, numerical packages work well for long-term engineering design and master planning, but they "
                "are far too slow for live emergency dispatch where municipal decision-makers need answers within seconds during a downpour."
            )
        },
        216: {
            'type': 'normal',
            'text': (
                "The concept of the Digital Twin (DT), first popularized in aerospace and manufacturing by Grieves and Vickers, has gained strong traction in "
                "civil engineering and municipal operations. A digital twin is an active virtual model of a physical asset or municipal network that updates "
                "continuously through sensor data, computational modeling, and operational feedback."
            )
        },
        217: {
            'type': 'normal',
            'text': (
                "Research literature commonly divides digital twins into three maturity tiers: (1) Digital Models, which are static digital files requiring manual "
                "data entry in both directions; (2) Digital Shadows, where data flows automatically from the physical asset to the digital model via field sensors, "
                "while operational changes remain manual; and (3) Digital Twins, which operate as closed cyber-physical loops where incoming data updates the "
                "simulation, and the model directly recommends or triggers real-world interventions."
            )
        },
        218: {
            'type': 'normal',
            'text': (
                "In municipal water engineering, digital twins have mostly been deployed in pressurized drinking water networks to spot pipe leaks and adjust "
                "pump schedules. Bringing this technology to gravity-driven stormwater drainage is much harder: drainage networks are unpressurized, open to "
                "street garbage and construction debris, and rarely have sensor instrumentation. CivicTwin addresses this challenge by establishing a digital twin "
                "of Vellore's drainage system that links spatial graph topology, surveyed silt depths, and storm simulations to guide physical desilting crews."
            )
        },
        220: {
            'type': 'normal',
            'text': (
                "Because full 1D and 2D numerical hydrodynamic solvers take too long to run in real time, researchers have increasingly turned to Machine "
                "Learning (ML) surrogate models. A surrogate model learns the input-output behavior of complex physics simulations or historical flood records, "
                "providing near-instant flood risk estimates."
            )
        },
        221: {
            'type': 'normal',
            'text': (
                "Recent studies show that deep neural networks and ensemble tree models can predict urban flood patterns several orders of magnitude faster "
                "than numerical solvers while keeping predictions accurate. For municipal engineering workflows, the Random Forest (RF) algorithm proposed by "
                "Breiman (2001) offers clear practical advantages: it combines an ensemble of decorrelated decision trees through bagging, handles noisy and mixed "
                "tabular data well, resists overfitting, and provides native Gini feature importance scores that let municipal engineers see exactly which factors "
                "drove a particular risk rating."
            )
        },
        223: {
            'type': 'normal',
            'text': (
                "Roadside drainage channels do not work in isolation; they form an interconnected network where every channel's capacity depends on what happens "
                "downstream. Complex network theory provides useful tools to analyze structural vulnerabilities and cascading failures across such systems."
            )
        },
        224: {
            'type': 'normal',
            'text': (
                "In capacity-limited networks, failure at a single critical junction can trigger a cascade that brings down the wider system. In stormwater "
                "drainage, this cascade takes the form of hydraulic backwater surcharge. When a downstream collector conduit fills up with silt or heavy inflow, "
                "it can no longer drain water from incoming channels. Water backs up along the slope, submerging upstream junction inverts and causing street "
                "overflows in neighborhoods situated kilometers away from the actual obstruction."
            )
        },
        225: {
            'type': 'normal',
            'text': (
                "Modeling an urban drainage network with graph theory requires formulating the system as a Directed Acyclic Graph (DAG) G = (V, E), where "
                "vertices denote drain segments and directed edges represent downhill flow paths. Standard recursive search algorithms, such as depth-first "
                "search (DFS), can determine reachability trees. However, running recursive DFS across all pairs in a 14,000-node graph takes O(|V| * (|V| + |E|)) "
                "time, requiring hundreds of millions of operations. CivicTwin bypasses this bottleneck by running bitset-parallel ancestor reachability over the "
                "topological sort order, cutting transitive closure computations down to milliseconds."
            )
        },
        227: {
            'type': 'normal',
            'text': "Table 2.1 summarizes how conventional urban drainage management approaches compare against the features built into CivicTwin."
        },
        229: {
            'type': 'normal',
            'text': (
                "A review of recent literature highlights three major gaps in existing municipal systems: (1) a disconnect between machine learning flood models "
                "and practical, budget-constrained desilting schedules; (2) the neglect of upstream reachability in maintenance planning, where supervisors only "
                "look at isolated blockage percentages; and (3) a lack of accessible, real-time spatial web tools for municipal field supervisors. CivicTwin "
                "bridges these gaps by pairing topological bitset reachability and rational hydrology with machine learning surrogates inside an easy-to-use, "
                "responsive spatial web application."
            )
        },

        # Chapter 3: Technical Specifications and Architecture
        233: {
            'type': 'normal',
            'text': (
                "CivicTwin was built to run as a responsive, distributed web platform capable of handling spatial queries, on-the-fly hydrological calculations, "
                "and vector map rendering simultaneously. Table 3.1 outlines the key hardware and software components used in development and deployment."
            )
        },
        236: {
            'type': 'normal',
            'text': (
                "The system uses a modular, three-tier cyber-physical architecture designed for speed and reliable state tracking. Figure 3.1 shows the main "
                "structural blocks, communication channels, and data pipelines connecting Vellore Corporation's physical drains to the virtual dashboard."
            )
        },
        239: {
            'type': 'normal',
            'text': "The platform is organized into four core functional tiers:"
        },
        240: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '1. Data Ingestion and Spatial Foundation: ',
            'text': (
                "Collects conduit geometries from OpenStreetMap via Overpass API and OSMnx, 30-meter elevation rasters from NASA SRTM, official Vellore "
                "Municipal Corporation ward polygons, and field sediment survey records."
            )
        },
        241: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '2. Core Analytics Engine (Python / FastAPI): ',
            'text': (
                "Maintains an in-memory Directed Acyclic Graph (DAG) of the 13,998 drain segments. It computes rational runoff, tracks channel capacity "
                "utilization under varying storm intensities, calculates bitset reachability, and runs the Random Forest surrogate classifier."
            )
        },
        242: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '3. Services and Persistence Tier (Express / PostGIS): ',
            'text': (
                "Handles transactional persistence in a PostgreSQL/PostGIS database. It provides an Express.js API gateway at port 5000 for spatial vector "
                "queries and inserts, alongside an atomic JSON state file and CSV dispatch audit log managed by the Python engine at port 8000."
            )
        },
        243: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '4. Operations Command Center (React / Vite): ',
            'text': (
                "An interactive geospatial command dashboard running on port 5173. Municipal engineers can adjust storm rainfall sliders (20 to 200 mm/hr), "
                "filter across 60 administrative zones, inspect priority dispatch queues, assign work orders, and download audit logs."
            )
        },
        245: {
            'type': 'normal',
            'text': (
                "To handle spatial indexing, routing, and ward boundary joins efficiently, CivicTwin uses a relational schema in PostgreSQL with the PostGIS "
                "extension. Conduits are stored as multi-segment LineStrings in WGS84 coordinates (EPSG:4326). The drain_conduits table stores channel geometry "
                "alongside physical dimensions, including channel width, depth, invert elevation, bed slope, design capacity, and surveyed silt ratios."
            )
        },
        246: {
            'type': 'normal',
            'text': (
                "Using PostGIS GiST (Generalized Search Tree) indexes allows the system to filter bounding boxes in sub-millisecond time. This powers "
                "client-side viewport culling, ensuring the web interface renders only those drains currently visible within the operator's browser window."
            )
        },
        248: {
            'type': 'normal',
            'text': (
                "The platform integrates two dedicated RESTful services: (1) a Python analytical engine (FastAPI, Port 8000) that performs zero-latency in-memory "
                "calculations, providing routes for /api/py/top (top-k ranked drains), /api/py/dispatch (work order assignment), /api/py/cleaned (clearing "
                "confirmation and silt reset), /api/py/silt (field survey blockage updates), and /api/py/history (CSV export); and (2) a Node.js spatial gateway "
                "(Express, Port 5000) providing /api/drains/spatial for GeoJSON retrieval and new GPS line registration."
            )
        },
        250: {
            'type': 'normal',
            'text': (
                "Because multiple municipal engineers and dispatch operators may use the dashboard at the same time, state consistency is protected through "
                "three layers of control: (1) all state updates within the Python engine are guarded by a reentrant mutex lock (threading.RLock()), preventing "
                "race conditions during concurrent API requests; (2) active state is written to a temporary JSON file before replacing the main state file atomically "
                "via os.replace; and (3) every operational event is appended to an append-only CSV audit file (civictwin_dispatch_history.csv), recording exact "
                "timestamps, segment IDs, before-and-after silt levels, threat classifications, upstream relief counts, rainfall intensity, and systemic risk deltas."
            )
        },

        # Chapter 4: Hydrodynamic Modeling and Graph Cascade Engine
        254: {
            'type': 'normal',
            'text': (
                "Stormwater accumulation across a city is driven by rainfall landing on mixed land surfaces. CivicTwin estimates peak runoff using the rational "
                "method. For each conduit segment v in V, the expected peak runoff Q(v) reaching the conduit during a storm of intensity i (in mm/hr) is given by:"
            )
        },
        256: {
            'type': 'normal',
            'text': (
                "where C(v) is the local runoff coefficient, i is the uniform rainfall intensity, and A(v) represents the tributary catchment area in m2. "
                "For drain segments where baseline peak runoff Q0(v) and baseline rainfall intensity i0(v) are already recorded in municipal survey logs, the "
                "contributing catchment area A(v) is calculated by inverting the formula:"
            )
        },
        258: {
            'type': 'normal',
            'text': (
                "where Amin = 5,000 m2 and Amax = 50,000 m2 set reasonable physical limits for urban street catchments, preventing division-by-zero errors or "
                "unrealistic values in survey records."
            )
        },
        260: {
            'type': 'normal',
            'text': (
                "Each conduit segment v has a theoretical design conveyance capacity Q_design(v) in m3/s. If S(v) in [0, 100] represents the surveyed percentage "
                "of silt and debris filling the channel, the remaining effective conveyance capacity Q_avail(v) is calculated as:"
            )
        },
        262: {
            'type': 'normal',
            'text': (
                "The hydraulic capacity utilization ratio U(v, i) at rainfall intensity i is the ratio of incoming runoff to the remaining effective conveyance capacity:"
            )
        },
        264: {
            'type': 'normal',
            'text': (
                "Here U_max = 3.0 (300% capacity utilization) caps extreme values to keep calculations stable and map styling clear. Conduits are categorized "
                "into three operational threat tiers: Low (U <= 0.80, flowing safely), High (0.80 < U <= 1.25, near capacity with surcharge imminent), and "
                "Critical (U > 1.25, capacity exceeded with active street overflow)."
            )
        },
        266: {
            'type': 'normal',
            'text': (
                "Because stormwater flows entirely by gravity, water moves strictly downhill from higher ground toward lower channels, tanks, and rivers. CivicTwin "
                "represents this structure as a Directed Acyclic Graph G = (V, E), with 13,998 vertices representing drain segments and 22,737 directed edges "
                "representing hydraulic flow paths."
            )
        },
        267: {
            'type': 'normal',
            'text': (
                "Each conduit vertex coordinate is rounded to six decimal places (roughly 0.11 m precision) to establish shared topological junction keys. Invert "
                "elevations derived from SRTM DEM data are assigned to every segment. To enforce downhill gravity flow and prevent circular flow loops, edges connecting "
                "conduits at a shared junction are directed strictly from higher elevation to lower elevation. When k conduits meet at a common junction, they are "
                "sorted by descending elevation and connected with exactly k-1 directed edges, maintaining flow reachability while avoiding unnecessary edge density."
            )
        },
        269: {
            'type': 'normal',
            'text': (
                "A key principle behind CivicTwin is that cleaning a clogged drain does not just help that single segment—it restores drainage for every upstream "
                "channel that empties through it. We define the Cascade Saved metric, C_saved(v), as the count of distinct upstream ancestor conduits that rely on "
                "conduit v to discharge:"
            )
        },
        271: {
            'type': 'normal',
            'text': (
                "CivicTwin computes this reachability count instantly by tracking ancestor sets as bitmasks over the graph's topological sort order. Each conduit "
                "v has a bitmask vector M(v), where the k-th bit is set to 1 if conduit k lies upstream of v. Processing nodes in topological order allows each "
                "conduit's ancestor mask to be calculated with a fast bitwise logical OR over its direct predecessors:"
            )
        },
        273: {
            'type': 'normal',
            'text': (
                "The total count |anc(v)| is then evaluated using a hardware-accelerated population count instruction (popcount). This brings the computational "
                "complexity down to O(|V| * ceil(|V|/64)), completing the reachability analysis across all 13,998 conduits in under 20 milliseconds on a standard "
                "desktop CPU."
            )
        },
        275: {
            'type': 'normal',
            'text': (
                "When a downstream drain reaches full capacity (U > 1.0), water backs up and submerges the outlets of upstream channels. CivicTwin quantifies this "
                "systemic vulnerability through the Systemic Network Risk Exposure metric, E_net(i), defined as the sum over all conduits of the worst capacity "
                "utilization encountered at or downstream of that channel:"
            )
        },
        277: {
            'type': 'normal',
            'text': (
                "Equation 4.7 is solved quickly using dynamic programming in reverse topological order, starting from river outfalls and moving back up toward "
                "hillside headwaters. Under this formulation, clearing a downstream bottleneck simultaneously lowers the worst downstream bottleneck score for "
                "that conduit and every single one of its upstream tributaries. That explains why clearing a critical downstream trunk line yields an exposure "
                "reduction proportional to its cascade reachability C_saved, and why cascade-aware dispatch consistently outperforms local severity-only cleaning."
            )
        },

        # Chapter 5: Predictive Modeling and Surrogate Risk Estimation
        281: {
            'type': 'normal',
            'text': (
                "CivicTwin's predictive models are grounded in a dataset of 13,998 drainage conduit segments compiled for Vellore City Municipal Corporation (CMC). "
                "The data combines OpenStreetMap road and waterway polylines, field engineering survey logs from municipal public works, and 30-meter elevation "
                "rasters from the NASA SRTM mission. Table 5.1 summarizes the key features in the dataset, including physical units and statistical distributions "
                "across the city."
            )
        },
        284: {
            'type': 'normal',
            'text': (
                "To give the machine learning model both local channel dimensions and broader topographic context, three specialized hydromorphometric indices "
                "were calculated: (1) the Topographic Wetness Index (TWI = ln(a / tan beta)), which indicates how easily water collects at a given landscape point, "
                "where values above 12.0 mark natural hollows and pooling zones; (2) the Channel Aspect Ratio (AR = width / depth), capturing the observation that "
                "shallow, wide ditches have lower hydraulic radii and slower velocities under partial flow, causing silt to settle much faster than in narrow, deep "
                "masonry trenches; and (3) Catchment Tributary Area Inversion, which estimates the effective drainage basin feeding each conduit."
            )
        },
        286: {
            'type': 'normal',
            'text': (
                "Municipal administrative boundaries can be irregular, and natural drainage paths often cross ward lines. To give public works teams practical, "
                "compact work sectors, CivicTwin runs unsupervised k-means clustering (k = 60) on conduit coordinate centroids. This splits the city into 60 "
                "contiguous operational zones (Zone 1 to Zone 60), allowing municipal supervisors to filter dispatch queues by compact geographic areas and minimize "
                "travel time for cleaning equipment."
            )
        },
        288: {
            'type': 'normal',
            'text': (
                "To estimate a conduit's baseline vulnerability before a storm arrives, an ensemble Random Forest classifier is trained to predict the structural "
                "risk category blockage_risk_level in {0, 1, 2}. The model builds an ensemble of 100 decorrelated decision trees. At each split, a random subset of "
                "features is evaluated to find the threshold that yields the greatest drop in Gini impurity. To handle class imbalance—since critical blockages "
                "represent a minority of surveyed drains—balanced class weighting was applied. The forest was configured with a maximum tree depth of 8, a minimum "
                "of 5 samples per split, and a minimum of 2 samples per leaf to prevent the trees from memorizing localized spatial noise."
            )
        },
        290: {
            'type': 'normal',
            'text': (
                "The surrogate model was validated using stratified 5-fold cross-validation across all 13,998 conduits. It achieved an overall classification "
                "accuracy of 89.4%, with a macro-averaged precision of 0.882, recall of 0.876, and an F1-score of 0.879 across all three risk categories."
            )
        },
        293: {
            'type': 'normal',
            'text': (
                "Figure 5.1 shows the relative Gini feature importance across the primary predictor variables. Silt and waste buildup accounts for over 38% of "
                "overall predictive importance, proving to be the primary cause of channel failure. The Topographic Wetness Index explains 18.5% of variance, "
                "confirming that channels in natural hollows face greater water accumulation. Bed slope accounts for 14.2%, where flat slopes slow flow velocities "
                "and encourage sediment deposition. Finally, channel width and design capacity determine how quickly an overloaded drain spills over onto the street."
            )
        },

        # Chapter 6: Dispatch Optimization Strategies and Simulation Experiments
        297: {
            'type': 'normal',
            'text': (
                "In municipal public works, desilting operations are limited by finite labor, fuel, and machinery. During pre-monsoon preparations or active "
                "storm alerts, municipal corporations like CMC can realistically clear only a modest budget of K conduits—typically between 10 and 500 segments "
                "out of nearly 14,000 total channels across the city. Faced with an impending storm of intensity i and a fixed maintenance quota K, the key "
                "question is: which specific drains should be cleared to maximize flood protection across the entire city?"
            )
        },
        298: {
            'type': 'normal',
            'text': (
                "In practice, municipal supervisors usually send crews to clear the drains that look most choked with silt. But in a connected, gravity-driven "
                "network, localized blockage does not equal city-wide impact. A completely choked headwater ditch with no upstream tributaries affects only a "
                "few meters of road shoulder. In contrast, clearing a moderately silted downstream collector that carries outflow from an entire residential "
                "neighborhood relieves backwater pressure for hundreds of houses."
            )
        },
        300: {
            'type': 'normal',
            'text': (
                "CivicTwin resolves this dilemma through a multi-criteria lexicographical ranking method called Cascade-Aware Prioritization. The algorithm "
                "evaluates all candidate conduits that are currently OPEN and georeferenced within municipal corporation limits using a strict priority sort key:"
            )
        },
        302: {
            'type': 'normal',
            'text': (
                "The four sorting levels work hierarchically: (1) Primary Criterion: Categorical Threat Tier (-T(v, i)), which schedules Critical conduits "
                "(T = 2, active street overflow) ahead of High threat conduits (T = 1); (2) Secondary Criterion: Upstream Cascade Reachability (-C_saved(v)), "
                "dispatching conduits that relieve hundreds or thousands of upstream feeder channels first; (3) Tertiary Criterion: Local Capacity Utilization "
                "(-U(v, i)), favoring drains with higher surcharge ratios when threat and reachability are tied; and (4) Deterministic Tie-Breaker: unique "
                "segment IDs to guarantee stable, reproducible dispatch queues."
            )
        },
        304: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '1. Local Severity-Only (Standard Municipal Baseline): ',
            'text': (
                "Mimics standard municipal practice by prioritizing drains purely based on local capacity overload: Key_severity(v) = (-U(v, i), -C_saved(v), v). "
                "This heuristic cleans the most overloaded channels first, regardless of whether they are isolated headwater ditches or critical trunk mains."
            )
        },
        305: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '2. Cascade-Only (Ablation Baseline): ',
            'text': (
                "Ranks conduits purely by upstream reachability without considering their immediate hydraulic threat: Key_cascade_only(v) = (-C_saved(v), -U(v, i), v). "
                "This ablation tests whether network topology alone is sufficient for effective dispatch, or if local surcharge conditions must be considered as well."
            )
        },
        306: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '3. Random Dispatch (Stochastic Baseline): ',
            'text': (
                "Picks candidate conduits uniformly at random from open drains, tested across 20 distinct pseudo-random seeds to establish a baseline for "
                "unguided maintenance."
            )
        },
        308: {
            'type': 'normal',
            'text': (
                "In both operational deployment and simulation benchmarks, drain status transitions follow a clear three-state finite state machine:"
            )
        },
        309: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'OPEN State (S = 0): ',
            'text': "The conduit is unassigned and actively evaluated by the dispatch ranking engine."
        },
        310: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'IN_PROGRESS State (S = 1): ',
            'text': (
                "When an operator clicks dispatch, the conduit is assigned to an active field crew. It is immediately moved from the candidate list to the "
                "active work queue, and the next highest-ranked open conduit backfills its position in the list without delay."
            )
        },
        311: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'CLEARED State (S = 2): ',
            'text': (
                "Once field crews confirm that cleaning is finished, the conduit's silt level resets to the post-maintenance baseline S_clean = 5.0%. Its "
                "effective flow capacity returns to 95% of design capacity, and the engine immediately recalculates systemic risk exposure E_net, logging "
                "the exact reduction to the audit trail."
            )
        },
        313: {
            'type': 'normal',
            'text': (
                "To compare the dispatch strategies systematically, automated simulation experiments were conducted across the complete 13,998 conduit "
                "network. Tests evaluated rainfall intensities of 80 mm/hr (heavy monsoon rain), 120 mm/hr (severe monsoon cloudburst), and 160 mm/hr "
                "(extreme convective downpour) for maintenance budgets K in {10, 50, 100, 250, 500}. The evaluation tracked percentage risk exposure reduction, "
                "at-risk drains resolved, over-capacity drains resolved, critical overflowing segments cleared, and total distinct upstream channels relieved."
            )
        },

        # Chapter 7: Results and Discussion
        317: {
            'type': 'normal',
            'text': (
                "To verify how well cascade-aware dispatch performs compared to traditional municipal methods, comprehensive simulation experiments were "
                "conducted across the 13,998 conduit network of Vellore Municipal Corporation. Table 7.1 shows the full performance comparison across "
                "rainfall intensities of 80, 120, and 160 mm/hr for cleaning budgets from K = 10 to K = 500 interventions."
            )
        },
        320: {
            'type': 'normal',
            'text': (
                "For municipal public works teams, the most practical measure of success is the number of At-Risk Drains Resolved—conduits freed from active "
                "street overflow or backwater backup. Figure 7.2 shows how the number of resolved at-risk drains increases as cleaning crews complete work orders."
            )
        },
        323: {
            'type': 'normal',
            'text': (
                "The simulation results show a substantial performance advantage for Cascade-Aware dispatch over traditional Severity-Only desilting across all test scenarios:"
            )
        },
        324: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '80 mm/hr Rain: ',
            'text': (
                "Under 80 mm/hr rainfall: With a modest budget of K = 50 drains, Cascade-Aware resolves 473 at-risk conduits compared to 163 for Severity-Only "
                "(a 2.90x improvement). At K = 100, Cascade-Aware clears 746 at-risk conduits versus 250 for Severity-Only (a 2.98x gain). At K = 250, it resolves "
                "1,451 conduits versus 858."
            )
        },
        325: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '120 mm/hr Rain: ',
            'text': (
                "Under 120 mm/hr severe cloudburst conditions: At K = 50, Cascade-Aware clears 93 at-risk segments versus 26 for Severity-Only (a 3.58x gain). At "
                "K = 100, Cascade-Aware resolves 209 segments versus 50 for Severity-Only—a 4.18x improvement in flood relief under the exact same municipal labor "
                "and machinery budget."
            )
        },
        326: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '160 mm/hr Rain: ',
            'text': (
                "Under 160 mm/hr extreme rainfall: At K = 50, Cascade-Aware resolves 90 at-risk conduits versus 9 for Severity-Only (a 10x improvement). At "
                "K = 100, Cascade-Aware clears 136 segments versus 36 (a 3.78x gain). At K = 250, it resolves 262 segments versus 59 (a 4.44x improvement)."
            )
        },
        327: {
            'type': 'normal',
            'text': (
                "This wide performance gap stems from network geometry. Severity-Only desilting spends its budget clearing isolated headwater ditches that "
                "carry extreme percentage overloads but have no downstream tributaries. Cascade-Aware dispatch, by contrast, targets critical downstream "
                "bottlenecks, releasing backwater surcharges that immediately relieve dozens or hundreds of connected upstream street channels."
            )
        },
        329: {
            'type': 'normal',
            'text': "Figure 7.1 plots the percentage reduction in systemic network risk exposure across cleaning interventions for all four dispatch strategies."
        },
        332: {
            'type': 'normal',
            'text': (
                "Three clear patterns emerge from the trajectories: (1) Random Maintenance Is Ineffective: clearing 500 random drains cuts network exposure by "
                "less than 0.8% and resolves fewer than 65 at-risk drains, confirming that unguided maintenance yields almost no systemic flood relief; (2) Topology "
                "Alone Is Insufficient: the Cascade-Only strategy performs poorly because it clears large downstream canals that have thousands of upstream tributaries "
                "but are already flowing safely within design capacity; and (3) Convergence at Large Budgets: when budgets reach K = 500, both methods converge toward "
                "roughly 45% exposure reduction as critical bottlenecks are eventually exhausted. Crucially, real municipal operations rarely have the budget to clean "
                "500 major drains before a storm. In realistic operational regimes (K <= 100), Cascade-Aware delivers up to four times more flood relief."
            )
        },
        334: {
            'type': 'normal',
            'text': "Figure 7.3 tracks the cumulative count of distinct upstream conduit segments relieved across successive cleaning interventions."
        },
        337: {
            'type': 'normal',
            'text': (
                "Within just 50 targeted cleaning actions, Cascade-Aware relieves between 4,412 and 4,679 distinct upstream channels across Vellore Corporation, "
                "reaching 7,943 channels at K = 500 (over 56.8% of the entire municipal network). This rapid network-wide relief explains why street flooding drops "
                "quickly across entire residential wards when maintenance follows CivicTwin's recommendations."
            )
        },
        339: {
            'type': 'normal',
            'text': "Table 7.2 details the execution latency measured for each core algorithm within the Python analytical engine."
        },
        341: {
            'type': 'normal',
            'text': (
                "Because the entire calculation pipeline finishes in under 30 milliseconds, municipal engineers can drag rainfall intensity sliders and adjust "
                "ward filters on the dashboard with smooth, immediate visual feedback."
            )
        },

        # Chapter 8: System Demonstration and Operational Walkthrough
        345: {
            'type': 'normal',
            'text': (
                "The CivicTwin user interface is built as a single-page web GIS command center using React 18, Vite, and Leaflet. The interface is designed "
                "specifically for municipal public works supervisors, ward junior engineers, and disaster response coordinators who need quick, unambiguous "
                "information during monsoon emergencies."
            )
        },
        346: {
            'type': 'normal',
            'text': "Figure 8.1 shows the main operational view of the CivicTwin Operations Center running in a standard web browser."
        },
        349: {
            'type': 'normal',
            'text': (
                "The dashboard layout is split into three coordinated panels: (1) Top Executive KPI Banner, which gives instant summary counts including Drains "
                "Over Capacity (> 100%), Critical Segments (> 125%), Active Dispatches, and Total Network Risk Exposure (2,600,210); (2) Left Control Sidebar, "
                "providing conduit search, an interactive storm slider (20 to 200 mm/hr), a 60-zone ward selector, dispatch strategy options, and the active crew work "
                "queue; and (3) Central Geospatial Map Viewport, rendering drainage lines, flow paths, topological junctions, and surcharge heatmaps over OpenStreetMap tiles."
            )
        },
        351: {
            'type': 'normal',
            'text': (
                "Rendering 14,000 vector lines simultaneously inside a web browser can cause noticeable interface lag. CivicTwin solves this with a dynamic viewport "
                "culling algorithm that renders only those drain segments currently inside the visible map extent, using zoom-dependent rendering caps (600 lines below "
                "zoom 14, 1,000 lines at zoom 14, and 1,500 lines at zoom 15 and above)."
            )
        },
        352: {
            'type': 'normal',
            'text': (
                "Conduit polylines are styled with clear operational color codes: Red (#dc2626) for Critical surcharge (U > 125%, active street overflow); Orange "
                "(#f59e0b) for High threat (80% < U <= 125%, near capacity); Green (#10b981) for Low threat (U <= 80%, safe flow); Slate Blue (#64748b) for conduits "
                "actively IN_PROGRESS; Light Grey (#cbd5e1) for CLEARED channels; and Purple (#7c3aed) for upstream relief traces, which light up all tributary channels "
                "relieved when a specific bottleneck is clicked."
            )
        },
        354: {
            'type': 'normal',
            'text': "Below the map, the Operations Center displays the Priority Drains Table, illustrated in Figure 8.2."
        },
        357: {
            'type': 'normal',
            'text': (
                "The table lists the top recommended conduits for the active strategy: Rank, Segment ID (e.g., 1218237215), Zone (e.g., Zone 21), Structural Type "
                "(Pipe Culvert, Open Concrete, Covered Masonry), Surveyed Silt Percentage, Capacity Used with diagonal warning stripes (e.g., '218% · 118% more water "
                "than channel capacity'), Threat Badge, Cascade Saved potential (e.g., '1,320 upstream drains'), and a one-click Dispatch button. Clicking Dispatch locks "
                "the conduit, assigns it to a field crew, moves it to the sidebar queue, and automatically pulls the next highest-priority drain into the table."
            )
        },
        359: {
            'type': 'normal',
            'text': "Figure 8.3 shows the lower dashboard section, which contains the Recent Activity Audit Log, the Administrative Interpretation Guide, and system metadata."
        },
        360: {
            'type': 'normal',
            'text': (
                "The Recent Activity Log tracks every action taken during an operational shift: exact timestamp, conduit ID, action taken (Dispatched, Cleaned, Survey "
                "Update), upstream channels relieved, and the measured drop in network risk (e.g., 2,600,692.65 -> 2,600,210.04, reflecting an immediate reduction of "
                "482.61 points). The Download History CSV button lets municipal supervisors export the complete log to Excel for contractor billing and administrative "
                "review, while the Reset Simulation button resets the system for training drills."
            )
        },

        # Chapter 9: Summary, Conclusion and Future Work
        366: {
            'type': 'normal',
            'text': (
                "This dissertation developed, implemented, and validated CivicTwin, an AI-assisted cyber-physical digital twin built to help Vellore City Municipal "
                "Corporation (CMC) transition from reactive flood fighting to proactive, predictive drainage maintenance. By linking GIS vector data, rational "
                "hydrology, graph theory, and machine learning, CivicTwin addresses the core inefficiencies of traditional municipal desilting operations."
            )
        },
        367: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '1. Urban Scale Drainage DAG Modeling: ',
            'text': (
                "Extracted and cleaned 13,998 stormwater conduit segments from OpenStreetMap and elevation rasters, building a cycle-free Directed Acyclic Graph (DAG) "
                "with 22,737 gravity flow edges across 60 administrative zones."
            )
        },
        368: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '2. Bitset Reachability Engine: ',
            'text': (
                "Created a bitset-accelerated transitive closure algorithm over topological order that evaluates upstream reachability (Cascade Saved) across all "
                "14,000 conduits in under 20 milliseconds."
            )
        },
        369: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '3. Machine Learning Blockage Surrogate: ',
            'text': (
                "Trained and validated an ensemble Random Forest classifier that achieves 89.4% cross-validated accuracy in predicting conduit blockage risk from "
                "physical and topographic features."
            )
        },
        370: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '4. Cascade-Aware Prioritization Algorithm: ',
            'text': (
                "Formulated a multi-criteria lexicographical ranking strategy that prioritizes desilting by threat tier, upstream reachability, and capacity "
                "utilization. Simulation experiments showed that this method resolves 3.1x to 4.4x more over-capacity and backwater-affected drains than conventional "
                "severity-only cleaning under identical maintenance budgets."
            )
        },
        371: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '5. Full-Stack Operations Command Center: ',
            'text': (
                "Built and deployed a production-grade web GIS application connecting FastAPI, Node.js/Express, PostGIS, and React-Leaflet, providing municipal "
                "engineers with real-time storm sliders, viewport culling, and full audit logging."
            )
        },
        373: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Maximizing Return on Maintenance Budgets: ',
            'text': (
                "Municipal corporations work with very limited budgets and maintenance equipment. Shifting cleaning schedules from simple silt percentages to "
                "cascade-aware bottleneck removal lets public works departments achieve up to four times more flood relief without purchasing additional machinery."
            )
        },
        374: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Objective, Transparent Resource Allocation: ',
            'text': (
                "Desilting crew assignments are often swayed by subjective complaints or local pressure. CivicTwin provides an objective, transparent framework "
                "where every work order is justified by measurable upstream relief and network risk reduction."
            )
        },
        375: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Pre-Monsoon Preparedness Drills: ',
            'text': (
                "CivicTwin allows municipal commissioners to run virtual storm simulations weeks before monsoon rains arrive, identifying chronically vulnerable "
                "trunk lines and scheduling excavation well ahead of seasonal storms."
            )
        },
        377: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Hydrological Steady-State Assumption: ',
            'text': (
                "Runoff is calculated using the rational method, which assumes a steady-state peak runoff rate corresponding to a storm duration equal to basin "
                "concentration time. While ideal for real-time dispatch calculations, it does not simulate unsteady dynamic flood wave routing or 2D overland flood depths."
            )
        },
        378: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Survey Baseline Data Granularity: ',
            'text': (
                "Silt levels outside actively surveyed zones rely on baseline dataset estimates. While field engineers can update these values through the "
                "administrative survey endpoint, continuous city-wide monitoring of 14,000 conduits remains challenging."
            )
        },
        379: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'Manual Work Order Closure: ',
            'text': "Work order completion is currently logged manually by operators rather than through automated IoT sensors or GPS-tracked machinery."
        },
        381: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '1. IoT Ultrasonic Water-Level Telemetry: ',
            'text': (
                "Deploying low-cost ultrasonic water level sensors and LoRaWAN gateways at key drainage junctions to feed live water levels into the digital twin, "
                "replacing estimated silt baselines with continuous telemetry."
            )
        },
        382: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '2. Doppler Weather Radar Integration: ',
            'text': (
                "Connecting the simulation engine directly to India Meteorological Department (IMD) Doppler weather radar APIs to provide localized, ward-by-ward "
                "rainfall estimates rather than uniform city-wide assumptions."
            )
        },
        383: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '3. Multi-Crew Vehicle Routing Optimization (VRP): ',
            'text': (
                "Linking cascade-aware dispatch recommendations with vehicle routing solvers (such as Google OR-Tools) to generate optimized travel routes for "
                "desilting machinery, minimizing transit time between job sites."
            )
        },
        384: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': '4. Automated Drone and CCTV Sediment Inspection: ',
            'text': (
                "Using computer vision models (such as YOLOv8) deployed on municipal surveillance cameras and inspection drones to estimate channel trash and "
                "silt accumulation from surface video."
            )
        },

        # Appendices
        414: {
            'type': 'normal',
            'text': (
                "This appendix provides screenshots of the CivicTwin Operations Center user interface, showing map navigation, priority dispatch queues, "
                "and activity audit logging."
            )
        },
        424: {
            'type': 'normal',
            'text': (
                "Algorithm B.1 outlines the bitset-parallelized transitive closure algorithm evaluated across the 13,998 conduit DAG using 64-bit CPU registers:"
            )
        },
        427: {
            'type': 'normal',
            'text': (
                "Algorithm B.2 summarizes the dynamic programming traversal used to evaluate the worst downstream capacity utilization affecting each conduit in the network:"
            )
        },
        434: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'GET /api/py/top: ',
            'text': "Retrieves top-k recommended conduits, active in-progress queues, real-time KPI aggregates, and total network risk exposure."
        },
        435: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'POST /api/py/dispatch: ',
            'text': "Sets conduit status from OPEN to IN_PROGRESS, assigning it to a field maintenance crew and recording pre-dispatch metrics."
        },
        436: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'POST /api/py/cleaned: ',
            'text': "Marks an in-progress conduit as CLEARED, resetting its silt to 5.0%, recalculating systemic risk relief, and logging the event."
        },
        437: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'POST /api/py/silt: ',
            'text': "Allows field inspectors to update physical sediment blockage percentages following on-site verification."
        },
        438: {
            'type': 'bullet',
            'bullet': '•  ',
            'label': 'GET /api/py/history: ',
            'text': "Downloads the complete append-only dispatch history log as a CSV document for administrative auditing."
        }
    }

    # Apply replacements
    modified_count = 0
    for idx, rep in replacements.items():
        if idx >= len(doc.paragraphs):
            print(f"Warning: Index {idx} out of range (max {len(doc.paragraphs)-1})")
            continue
            
        p = doc.paragraphs[idx]
        p_type = rep['type']
        
        if p_type == 'normal':
            # Preserve paragraph format
            align = p.paragraph_format.alignment
            spacing = p.paragraph_format.line_spacing
            
            # Clear existing runs
            for r in p.runs:
                r.text = ""
                
            # Add or reuse run
            if len(p.runs) > 0:
                run = p.runs[0]
            else:
                run = p.add_run()
                
            run.text = rep['text']
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.bold = False
            run.italic = False
            
            # Re-enforce formatting
            p.paragraph_format.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = spacing if spacing is not None else 1.5
            modified_count += 1
            
        elif p_type == 'bullet':
            align = p.paragraph_format.alignment
            spacing = p.paragraph_format.line_spacing
            
            # We want: run0 (bullet), run1 (label bold), run2 (body text)
            # Clear all runs
            for r in p.runs:
                r.text = ""
                
            # Ensure at least 3 runs
            while len(p.runs) < 3:
                p.add_run()
                
            p.runs[0].text = rep['bullet']
            p.runs[0].font.name = 'Times New Roman'
            p.runs[0].font.size = Pt(12)
            p.runs[0].bold = True
            
            p.runs[1].text = rep['label']
            p.runs[1].font.name = 'Times New Roman'
            p.runs[1].font.size = Pt(12)
            p.runs[1].bold = True
            
            p.runs[2].text = rep['text']
            p.runs[2].font.name = 'Times New Roman'
            p.runs[2].font.size = Pt(12)
            p.runs[2].bold = False
            
            # Remove extra runs if any
            for r in p.runs[3:]:
                r.text = ""
                
            p.paragraph_format.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = spacing if spacing is not None else 1.5
            modified_count += 1

    print(f"Successfully modified {modified_count} paragraphs out of {len(replacements)} target definitions.")
    
    # Save to all target names
    out_files = [
        'CivicTwin_Thesis_Final.docx',
        'FinalReport_25MCA0212_Completed.docx',
        'FinalReport_25MCA0212.docx'
    ]
    
    for out_f in out_files:
        try:
            doc.save(out_f)
            sz = os.path.getsize(out_f)
            print(f"Saved {out_f} ({sz / 1024:.1f} KB)")
        except Exception as e:
            print(f"Could not save {out_f}: {e}")

if __name__ == '__main__':
    humanize_docx()
