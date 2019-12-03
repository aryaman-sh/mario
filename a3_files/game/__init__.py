"""CSSE1001 Game Engine

The CSSE1001 Game Engine was designed and developed by Benjamin Martin in 2019 to provide
a basis for the development of 2d sandbox style games for assignments. Other course staff
have added minor extensions and made stylistic changes since the initial version.

The Game Engine depends on the pymunk python physics library and renders games using
the tkinter library.

All future works based upon this work must credit the original author, Benjamin Martin,
 using the Python  __author__ field in every relevant file, including but not limited to:
	1) the orignal author's direct work,
	2) a modified version of the original author's work,
	3) an extension of the engine that copies any of the architecture that the
	   original author designed
"""

__version__ = "1.0.1"
__author__ = "Benjamin Martin"
__copyright__ = "The University of Queensland, 2019"

__all__ = ["block", "item", "entity", "mob", "util", "view", "world"]
