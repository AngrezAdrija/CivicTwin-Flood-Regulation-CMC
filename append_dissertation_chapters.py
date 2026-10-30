import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from generate_thesis_docx import (
    add_p, add_bullet, add_chapter_heading, add_section_heading, 
    add_subsection_heading, add_figure, add_table_caption, add_equation, format_cell
)

def add_frontmatter_lists(doc):
    # Table of Contents placeholder / outline
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("TABLE OF CONTENTS")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    toc_data = [
        ("Declaration", "iii"),
        ("Certificate", "iv"),
        ("Acknowledgement", "v"),
        ("Executive Summary", "vi"),
        ("Table of Contents", "vii"),
        ("List of Figures", "viii"),
        ("List of Tables", "ix"),
        ("List of Abbreviations", "x"),
        ("Symbols and Notations", "xi"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1 Background and Context", "1"),
        ("    1.2 Problem Statement", "3"),
        ("    1.3 Project Objectives", "4"),
        ("    1.4 Motivation and Societal Impact", "5"),
        ("    1.5 Scope and Delimitations", "6"),
        ("    1.6 Dissertation Organization", "7"),
        ("CHAPTER 2: LITERATURE REVIEW", "8"),
        ("    2.1 Urban Stormwater Infrastructure and Hydraulic Modeling", "8"),
        ("    2.2 Digital Twins in Civil and Municipal Engineering", "11"),
        ("    2.3 Machine Learning Surrogates in Flood Risk Assessment", "13"),
        ("    2.4 Complex Network Theory and Cascading Failures in Urban Utilities", "16"),
        ("    2.5 Critical Analysis and Research Gaps", "18"),
        ("CHAPTER 3: TECHNICAL SPECIFICATIONS AND ARCHITECTURE", "21"),
        ("    3.1 System Requirements and Specifications", "21"),
        ("    3.2 High-Level System Architecture", "23"),
        ("    3.3 Spatial Data Modeling and PostGIS Database Schema", "26"),
        ("    3.4 RESTful API Architecture and Endpoints", "28"),
        ("    3.5 Concurrency Control and Audit Trail Logging", "30"),
        ("CHAPTER 4: HYDRODYNAMIC MODELING AND GRAPH CASCADE ENGINE", "32"),
        ("    4.1 Hydrological Formulation and Catchment Inversion", "32"),
        ("    4.2 Effective Capacity and Utilisation Formulation", "34"),
        ("    4.3 Directed Acyclic Graph (DAG) Construction", "37"),
        ("    4.4 Bitset-Accelerated Ancestor Reachability", "40"),
        ("    4.5 Systemic Network Risk Exposure Metric", "43"),
        ("CHAPTER 5: PREDICTIVE MODELING AND SURROGATE RISK ESTIMATION", "46"),
        ("    5.1 Dataset Profiling and Preprocessing", "46"),
        ("    5.2 Feature Engineering and Hydromorphometric Indices", "49"),
        ("    5.3 Spatial Clustering and Ward Demarcation", "51"),
        ("    5.4 Random Forest Surrogate Formulation", "53"),
        ("    5.5 Model Evaluation and Feature Importance", "56"),
        ("CHAPTER 6: DISPATCH OPTIMIZATION STRATEGIES AND SIMULATION EXPERIMENTS", "59"),
        ("    6.1 The Municipal Resource Allocation Dilemma", "59"),
        ("    6.2 Proposed Cascade-Aware Dispatch Strategy", "61"),
        ("    6.3 Comparative Baseline Strategies and Ablation Formulations", "63"),
        ("    6.4 Closed-Loop Simulation Lifecycle and Feedback Dynamics", "65"),
        ("    6.5 Simulation Experimental Design", "68"),
        ("CHAPTER 7: RESULTS AND DISCUSSION", "71"),
        ("    7.1 Quantitative Performance Benchmarking", "71"),
        ("    7.2 Analysis of At-Risk and Backwater Flood Resolution", "74"),
        ("    7.3 Network Risk Exposure Trajectories", "77"),
        ("    7.4 Reachability Impact and Upstream Relief", "80"),
        ("    7.5 Computational Latency and Scalability", "82"),
        ("CHAPTER 8: SYSTEM DEMONSTRATION AND OPERATIONAL WALKTHROUGH", "85"),
        ("    8.1 CivicTwin Operations Center Interface Overview", "85"),
        ("    8.2 Interactive Geospatial Map and Dynamic Viewport Rendering", "87"),
        ("    8.3 Priority Dispatch Table and Live Surcharge Metrics", "90"),
        ("    8.4 Field Work Order Lifecycle and Operational Audit Trails", "93"),
        ("CHAPTER 9: SUMMARY, CONCLUSION AND FUTURE WORK", "96"),
        ("    9.1 Summary of Research Contributions", "96"),
        ("    9.2 Practical Implications for Municipal Public Works", "98"),
        ("    9.3 Limitations of the Current Study", "100"),
        ("    9.4 Future Research Directions", "101"),
        ("REFERENCES", "103"),
        ("APPENDIX A: SYSTEM USER INTERFACE DEMONSTRATION", "108"),
        ("APPENDIX B: CORE MATHEMATICAL ALGORITHMS", "112"),
        ("APPENDIX C: DATABASE DDL AND API SPECIFICATIONS", "116"),
    ]
    
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(5.0)
    table.columns[1].width = Inches(1.0)
    format_cell(table.rows[0].cells[0], "Title", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(table.rows[0].cells[1], "Page No.", bold=True, font_size=11, align=WD_ALIGN_PARAGRAPH.RIGHT, fill_hex="E2E8F0")
    
    for item, pg in toc_data:
        row = table.add_row()
        bold = item.startswith("CHAPTER") or item in ("Declaration", "Certificate", "Acknowledgement", "Executive Summary", "REFERENCES")
        format_cell(row.cells[0], item, bold=bold, font_size=10)
        format_cell(row.cells[1], pg, bold=bold, font_size=10, align=WD_ALIGN_PARAGRAPH.RIGHT)
        
    # List of Figures
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("LIST OF FIGURES")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    fig_data = [
        ("Fig. 3.1", "CivicTwin Multi-Tier System Architecture and Data Pipelines", "24"),
        ("Fig. 5.1", "Gini Feature Importance of Top Predictors for Drainage Blockage Vulnerability", "57"),
        ("Fig. 6.1", "Conduit Operational State Lifecycle in CivicTwin", "66"),
        ("Fig. 7.1", "Network Risk Exposure Reduction (%) Across Cleaning Interventions", "78"),
        ("Fig. 7.2", "Comparative Resolution of At-Risk Conduits Across Storm Intensities", "75"),
        ("Fig. 7.3", "Distinct Upstream Conduits Relieved Across Cleaning Interventions", "81"),
        ("Fig. 8.1", "CivicTwin Operations Center Command Dashboard and Geospatial Map", "86"),
        ("Fig. 8.2", "Priority Dispatch Table with Real-Time Capacity Surcharge Metrics", "91"),
        ("Fig. 8.3", "Recent Operational Activity Audit Log and Administrative Guide", "94"),
        ("Fig. A.1", "Full CivicTwin Operations Center Interface Showing GIS Map and Live KPI Counters", "109"),
        ("Fig. A.2", "Priority Drains Table Showing Surcharge Ratios and Upstream Reachability", "110"),
        ("Fig. A.3", "Activity Audit Log and Administrative Metric Interpretation Guidelines", "111"),
    ]
    
    tbl_f = doc.add_table(rows=1, cols=3)
    tbl_f.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_f.autofit = False
    tbl_f.columns[0].width = Inches(1.2)
    tbl_f.columns[1].width = Inches(4.0)
    tbl_f.columns[2].width = Inches(0.8)
    format_cell(tbl_f.rows[0].cells[0], "Figure No.", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_f.rows[0].cells[1], "Title", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_f.rows[0].cells[2], "Page No.", bold=True, font_size=11, align=WD_ALIGN_PARAGRAPH.RIGHT, fill_hex="E2E8F0")
    for fn, ft, fp in fig_data:
        r = tbl_f.add_row()
        format_cell(r.cells[0], fn, font_size=10, bold=True)
        format_cell(r.cells[1], ft, font_size=10)
        format_cell(r.cells[2], fp, font_size=10, align=WD_ALIGN_PARAGRAPH.RIGHT)
        
    # List of Tables
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("LIST OF TABLES")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    tbl_data = [
        ("Table 2.1", "Comparative Analysis of Urban Drainage Management Paradigms", "19"),
        ("Table 3.1", "System Hardware and Software Specifications", "22"),
        ("Table 5.1", "Dataset Feature Profiles for CMC Drainage Conduits (N = 13,998)", "47"),
        ("Table 7.1", "Comparative Dispatch Strategy Performance Across Storm Regimes", "72"),
        ("Table 7.2", "Analytical Engine Algorithmic Runtime Profiles (N = 13,998)", "83"),
    ]
    tbl_t = doc.add_table(rows=1, cols=3)
    tbl_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t.autofit = False
    tbl_t.columns[0].width = Inches(1.2)
    tbl_t.columns[1].width = Inches(4.0)
    tbl_t.columns[2].width = Inches(0.8)
    format_cell(tbl_t.rows[0].cells[0], "Table No.", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_t.rows[0].cells[1], "Title", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_t.rows[0].cells[2], "Page No.", bold=True, font_size=11, align=WD_ALIGN_PARAGRAPH.RIGHT, fill_hex="E2E8F0")
    for tn, tt, tp in tbl_data:
        r = tbl_t.add_row()
        format_cell(r.cells[0], tn, font_size=10, bold=True)
        format_cell(r.cells[1], tt, font_size=10)
        format_cell(r.cells[2], tp, font_size=10, align=WD_ALIGN_PARAGRAPH.RIGHT)
        
    # List of Abbreviations
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("LIST OF ABBREVIATIONS")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    abbr_data = [
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("CMC", "City Municipal Corporation (Vellore Corporation)"),
        ("CPS", "Cyber-Physical System"),
        ("DAG", "Directed Acyclic Graph"),
        ("DEM", "Digital Elevation Model"),
        ("EPA", "Environmental Protection Agency"),
        ("EPSG", "European Petroleum Survey Group"),
        ("GIS", "Geographic Information System"),
        ("IoT", "Internet of Things"),
        ("JSON", "JavaScript Object Notation"),
        ("KPI", "Key Performance Indicator"),
        ("ML", "Machine Learning"),
        ("MSL", "Mean Sea Level"),
        ("OSM", "OpenStreetMap"),
        ("PostGIS", "PostgreSQL Spatial Object Extension"),
        ("REST", "Representational State Transfer"),
        ("RF", "Random Forest"),
        ("SRTM", "Shuttle Radar Topography Mission"),
        ("SWMM", "Storm Water Management Model"),
        ("TWI", "Topographic Wetness Index"),
        ("UI", "User Interface"),
        ("WGS84", "World Geodetic System 1984"),
    ]
    tbl_a = doc.add_table(rows=1, cols=2)
    tbl_a.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_a.autofit = False
    tbl_a.columns[0].width = Inches(2.0)
    tbl_a.columns[1].width = Inches(4.0)
    format_cell(tbl_a.rows[0].cells[0], "Abbreviation", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_a.rows[0].cells[1], "Expansion", bold=True, font_size=11, fill_hex="E2E8F0")
    for an, ae in abbr_data:
        r = tbl_a.add_row()
        format_cell(r.cells[0], an, font_size=10, bold=True)
        format_cell(r.cells[1], ae, font_size=10)
        
    # Symbols and Notations
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("SYMBOLS AND NOTATIONS")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    
    sym_data = [
        ("Q", "Peak stormwater runoff discharge rate", "m3/s"),
        ("C", "Catchment surface runoff coefficient", "Dimensionless"),
        ("i", "Rainfall storm precipitation intensity", "mm/hr"),
        ("A", "Tributary catchment contributing area", "m2"),
        ("Q_design", "Unobstructed design conveyance capacity", "m3/s"),
        ("S", "Silt and solid waste sediment blockage", "%"),
        ("Q_avail", "Effective hydraulic capacity post-silt reduction", "m3/s"),
        ("U", "Hydraulic capacity utilisation ratio (Q / Q_avail)", "Dimensionless"),
        ("G = (V, E)", "Directed Acyclic Graph of drainage network", "---"),
        ("V", "Vertex set of drainage conduit segments (n = 13,998)", "---"),
        ("E", "Directed edge set of downhill flow links (m = 22,737)", "---"),
        ("pred(v)", "Immediate upstream hydraulic predecessors of node v", "---"),
        ("succ(v)", "Immediate downstream hydraulic successors of node v", "---"),
        ("anc(v)", "Set of all transitive upstream ancestor conduits of node v", "---"),
        ("desc(v)", "Set of all transitive downstream descendant conduits of node v", "---"),
        ("C_saved(v)", "Cascade reachability relief count (|anc(v)|)", "Conduits"),
        ("E_net", "Systemic network risk exposure summation", "%"),
        ("T(v)", "Categorical threat tier (0 = Low, 1 = High, 2 = Critical)", "Discrete"),
        ("K", "Municipal maintenance clearing budget", "Conduits"),
        ("z", "Terrain invert elevation above MSL", "m"),
    ]
    tbl_s = doc.add_table(rows=1, cols=3)
    tbl_s.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_s.autofit = False
    tbl_s.columns[0].width = Inches(1.8)
    tbl_s.columns[1].width = Inches(3.2)
    tbl_s.columns[2].width = Inches(1.0)
    format_cell(tbl_s.rows[0].cells[0], "Symbol", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_s.rows[0].cells[1], "Description", bold=True, font_size=11, fill_hex="E2E8F0")
    format_cell(tbl_s.rows[0].cells[2], "Unit", bold=True, font_size=11, fill_hex="E2E8F0")
    for sn, sd, su in sym_data:
        r = tbl_s.add_row()
        format_cell(r.cells[0], sn, font_size=10, bold=True)
        format_cell(r.cells[1], sd, font_size=10)
        format_cell(r.cells[2], su, font_size=10)
        
    print("Frontmatter lists added.")

print("append_dissertation_chapters module loaded.")
