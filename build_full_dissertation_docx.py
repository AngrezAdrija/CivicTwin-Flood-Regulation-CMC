import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from generate_thesis_docx import (
    add_p, add_bullet, add_chapter_heading, add_section_heading, 
    add_subsection_heading, add_figure, add_table_caption, add_equation, format_cell
)

def update_dissertation():
    doc_path = 'FinalReport_25MCA0212.docx'
    print(f"Loading {doc_path}...")
    doc = docx.Document(doc_path)
    
    # 1. Enforce strict VIT Margins on all sections: Left 1.5 in, Right 1.0 in, Top 1.0 in, Bottom 1.0 in
    for s in doc.sections:
        s.left_margin = Inches(1.5)
        s.right_margin = Inches(1.0)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
    print("Enforced 1.5in Left, 1.0in Right/Top/Bottom margins across all sections.")
    
    # 2. Fix Acknowledgement placeholder
    ack_fixed = False
    for p in doc.paragraphs:
        if '< Domain or dissertation' in p.text or '< Domain' in p.text:
            p.text = p.text.replace('< Domain or dissertation / internship area >', 
                                    'Urban Hydro-informatics, Cyber-Physical Systems, and Digital Twins for Urban Infrastructure Resilience')
            p.text = p.text.replace('for his/her constant guidance', 'for her constant guidance')
            p.text = p.text.replace('My association with him/her', 'My association with her')
            # Reformat font
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(12)
            ack_fixed = True
    print(f"Acknowledgement placeholder fixed: {ack_fixed}")
    
    # 3. Replace Executive Summary placeholder
    summary_text = (
        "Rapid, unplanned urbanization and recurrent high-intensity monsoon precipitation severely overwhelm aging stormwater "
        "drainage infrastructures across tier-two Indian municipalities, culminating in systemic waterlogging, structural asset degradation, "
        "and public paralysis. Conventional municipal public works operate reactively, deploying desilting crews primarily in response to "
        "localized citizen grievances or visible surface overflow while neglecting topological connectivity and backwater surcharge dynamics. "
        "This dissertation presents CivicTwin, an AI-enabled cyber-physical digital twin developed for predictive urban drainage management "
        "and proactive flood resilience in Vellore City Municipal Corporation (CMC). CivicTwin formulates 13,998 drain conduits across 60 spatial "
        "zones into a Directed Acyclic Graph (DAG) comprising 22,737 hydraulic edges. Integrating the rational runoff method, an ensemble Random Forest "
        "blockage surrogate, and a bitset-accelerated reachability engine, CivicTwin introduces a multi-criteria cascade-aware dispatch strategy. "
        "Across simulated rainfall intensities from 80 to 160 mm/hr, the proposed cascade-aware method resolves between 3.1x and 4.4x more at-risk and "
        "backwater-threatened conduits than traditional severity-only desilting under identical municipal clearing budgets. Implemented as an "
        "interactive web GIS command dashboard connecting FastAPI, React-Leaflet, and PostgreSQL/PostGIS, CivicTwin provides municipal administrators "
        "with real-time hydraulic bottleneck foresight, maximizing labor productivity and transforming municipal disaster response into predictive urban resilience."
    )
    
    exec_found = False
    for p in doc.paragraphs:
        if 'Summary of the dissertation / internship for one page and not exceeding 200 words' in p.text:
            p.text = summary_text
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(12)
            exec_found = True
    print(f"Executive summary populated: {exec_found}")
    
    # Clear trailing empty paragraphs after the executive summary
    # Find index of executive summary paragraph
    exec_idx = -1
    for i, p in enumerate(doc.paragraphs):
        if "CivicTwin, an AI-enabled cyber-physical digital twin" in p.text:
            exec_idx = i
            break
            
    if exec_idx != -1:
        # Delete paragraphs after exec_idx
        p_elems_to_delete = [p._p for p in doc.paragraphs[exec_idx+1:]]
        for p_elem in p_elems_to_delete:
            p_elem.getparent().remove(p_elem)
        print(f"Cleared trailing empty paragraphs after paragraph index {exec_idx}.")
        
    return doc

print("update_dissertation defined.")
