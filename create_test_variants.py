"""Convenience runner for generating audio test variants.

Example:
    python create_test_variants.py test_audio/curated/clean/clean_male_01.wav
"""

import sys
from tools.create_variants import main

if __name__ == "__main__":
    main()
