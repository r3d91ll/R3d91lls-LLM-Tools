import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.offsetbox import AnnotationBbox, TextArea

def add_flowchart_element(ax, text, xy, xytext, xyarrow, width=1.5, height=0.6):
    """
    Add a flowchart element with an arrow to the plot.
    """
    # Create a text box
    text_box = TextArea(text)
    ab = AnnotationBbox(text_box, xy,
                        xybox=xytext,
                        xycoords='data',
                        boxcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='black'),
                        pad=0.3)
    ax.add_artist(ab)

    # Create a rectangle
    rect = mpatches.FancyBboxPatch(xyarrow, width, height, boxstyle="round,pad=0.3", ec="black", fc="white", lw=1)
    ax.add_patch(rect)

def create_flowchart():
    """
    Create a flowchart based on the provided Bash script structure.
    """
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.axis('off')

    # Variable Definitions
    add_flowchart_element(ax, "Variable Definitions", (5, 19), (-30, 40), (4.25, 18.7))

    # Functions
    add_flowchart_element(ax, "prepare_report Function", (5, 17), (-100, 40), (4.25, 16.7))
    add_flowchart_element(ax, "generate_report Function", (5, 15), (50, 40), (4.25, 14.7))

    # Determine Package Manager
    add_flowchart_element(ax, "Determine Package Manager (PAKMAN)", (5, 13), (-30, 40), (4.25, 12.7))

    # Common Preparation Steps
    add_flowchart_element(ax, "Run prepare_report", (5, 11), (-30, 40), (4.25, 10.7))

    # Package Manager Specific Commands
    add_flowchart_element(ax, "Package Manager Specific Commands & generate_report", (5, 9), (-100, 40), (4.25, 8.7), width=4)

    # End
    add_flowchart_element(ax, "End", (5, 7), (30, 40), (4.25, 6.7))

    plt.title('Flowchart of Bash Script', fontsize=16)
    plt.show()

create_flowchart()
