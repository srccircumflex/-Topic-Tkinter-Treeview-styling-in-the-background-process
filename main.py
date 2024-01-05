try:
    from sys import path
    from pathlib import Path

    path.append(str(Path(__file__).parent))
except:
    raise

from base.treeselect import StructureNode
from treeselectpopup import popup

if __name__ == '__main__':
    structure = (
        StructureNode("L0", "V0",
                      StructureNode("L0-0", "V0-0"),
                      StructureNode("L0-1", "V0-1"),
                      StructureNode("L0-2", "V0-2"),
                      ),
        StructureNode("L1", "V1"),
        StructureNode("L2", "V2",
                      StructureNode("L2-0", "V2-0",
                                    StructureNode("L2-0-0", "V2-0-0"),
                                    StructureNode("L2-0-1", "V2-0-1"),
                                    StructureNode("L2-0-2", "V2-0-2"),
                                    ),
                      StructureNode("L2-1", "V2-1"),
                      ),
    )
    data = server = popup(*structure)
    print(data)