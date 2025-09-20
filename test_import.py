"""
Mini test script to verify module imports
"""

import sys
import os

# Aggiungi la directory corrente al path per importazioni relative
sys.path.insert(0, os.path.abspath('.'))

try:
    # Importa solo il router stats
    from app.api.routes import stats
    print(f"Router esiste? {hasattr(stats, 'router')}")
    print(f"Router type: {type(stats.router)}")
    print("Importazione riuscita!")
except Exception as e:
    print(f"Errore di importazione: {str(e)}")
    import traceback
    traceback.print_exc()
