import os
import sys
import docx
from build_full_dissertation_docx import update_dissertation
from append_dissertation_chapters import add_frontmatter_lists
from append_chapters_1_to_9 import add_all_dissertation_chapters

def main():
    base_file = 'FinalReport_25MCA0212_backup.docx' if os.path.exists('FinalReport_25MCA0212_backup.docx') else 'FinalReport_25MCA0212.docx'
    print(f"=== Step 1: Loading base document from {base_file} ===")
    
    # Custom update from base_file
    doc = docx.Document(base_file)
    
    # 1. Enforce strict VIT Margins
    for s in doc.sections:
        s.left_margin = docx.shared.Inches(1.5)
        s.right_margin = docx.shared.Inches(1.0)
        s.top_margin = docx.shared.Inches(1.0)
        s.bottom_margin = docx.shared.Inches(1.0)
    print("Enforced 1.5in Left, 1.0in Right/Top/Bottom margins across all sections.")
    
    # 2. Fix Acknowledgement placeholder
    ack_fixed = False
    for p in doc.paragraphs:
        if '< Domain or dissertation' in p.text or '< Domain' in p.text:
            p.text = p.text.replace('< Domain or dissertation / internship area >', 
                                    'Urban Hydro-informatics, Cyber-Physical Systems, and Digital Twins for Urban Infrastructure Resilience')
            p.text = p.text.replace('for his/her constant guidance', 'for her constant guidance')
            p.text = p.text.replace('My association with him/her', 'My association with her')
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = docx.shared.Pt(12)
            ack_fixed = True
    print(f"Acknowledgement placeholder fixed: {ack_fixed}")
    
    # 3. Replace Executive Summary placeholder
    summary_text = (
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
    
    for p in doc.paragraphs:
        if 'Summary of the dissertation / internship for one page and not exceeding 200 words' in p.text:
            p.text = summary_text
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = docx.shared.Pt(12)
                
    exec_idx = -1
    for i, p in enumerate(doc.paragraphs):
        if "CivicTwin, an AI-enabled cyber-physical digital twin" in p.text:
            exec_idx = i
            break
            
    if exec_idx != -1:
        p_elems_to_delete = [p._p for p in doc.paragraphs[exec_idx+1:]]
        for p_elem in p_elems_to_delete:
            p_elem.getparent().remove(p_elem)
        print(f"Cleared trailing empty paragraphs after paragraph index {exec_idx}.")
    
    print("=== Step 2: Adding Frontmatter lists (TOC, Figures, Tables, Abbreviations, Symbols) ===")
    add_frontmatter_lists(doc)
    
    print("=== Step 3: Adding Chapters 1 to 9, References, and Appendices ===")
    add_all_dissertation_chapters(doc)
    
    completed_path = 'FinalReport_25MCA0212_Completed.docx'
    print(f"=== Step 4: Saving updated document to {completed_path} ===")
    doc.save(completed_path)
    file_size = os.path.getsize(completed_path)
    print(f"SUCCESS! {completed_path} generated successfully! Size: {file_size / 1024:.1f} KB ({file_size} bytes)")
    
    # Try saving to FinalReport_25MCA0212.docx if unlocked
    try:
        doc.save('FinalReport_25MCA0212.docx')
        print("Also overwritten FinalReport_25MCA0212.docx successfully!")
    except PermissionError:
        print("Note: FinalReport_25MCA0212.docx is currently open in Word. Saved to FinalReport_25MCA0212_Completed.docx.")

if __name__ == '__main__':
    main()
