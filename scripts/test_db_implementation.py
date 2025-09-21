#!/usr/bin/env python3
"""
Test dell'implementazione del database SQLite per i documenti.
Questo script esegue test di base sul DocumentDatabase e sul MetadataStoreManager
basato su database per verificare che le funzionalità chiave funzionino correttamente.
"""

import os
import sys
import json
import tempfile
import unittest
import logging
import shutil
from pathlib import Path

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("db_test")

# Aggiungi il percorso principale al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa le classi da testare
try:
    from app.utils.document_database import DocumentDatabase
    from app.utils.document_manager import DocumentManager
except ImportError as e:
    logger.error(f"Errore di importazione: {e}")
    logger.error("Verifica che gli script siano nel percorso corretto e che i moduli siano disponibili.")
    sys.exit(1)

class TestDocumentDatabase(unittest.TestCase):
    """Test per la classe DocumentDatabase."""
    
    def setUp(self):
        """Configura l'ambiente di test."""
        # Crea una directory temporanea per i test
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"Directory test creata: {self.test_dir}")
        
        # Crea un file JSON di test
        self.test_docs = {
            "doc1": {
                "id": "doc1",
                "filename": "test1.pdf",
                "title": "Test Document 1",
                "path": "/path/to/test1.pdf",
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
                "metadata": {"pages": 5, "author": "Test Author"}
            },
            "doc2": {
                "id": "doc2",
                "filename": "test2.pdf",
                "title": "Test Document 2",
                "path": "/path/to/test2.pdf",
                "created_at": "2023-01-02T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "metadata": {"pages": 10, "author": "Another Author"}
            }
        }
        
        # Scrivi il JSON di test
        json_path = os.path.join(self.test_dir, "documents.json")
        with open(json_path, 'w') as f:
            json.dump(self.test_docs, f)
        
        logger.info(f"File JSON di test creato: {json_path}")
        
        # Inizializza il database
        self.db = DocumentDatabase(data_dir=self.test_dir)
    
    def tearDown(self):
        """Pulisce dopo i test."""
        # Chiudi il database
        if hasattr(self, 'db') and self.db:
            self.db.close()
        
        # Rimuovi la directory temporanea
        shutil.rmtree(self.test_dir)
        logger.info(f"Directory test rimossa: {self.test_dir}")
    
    def test_init_db(self):
        """Testa l'inizializzazione del database."""
        # Verifica che il file del database sia stato creato
        db_path = os.path.join(self.test_dir, "documents.db")
        self.assertTrue(os.path.exists(db_path), "Il file del database non è stato creato")
        
        # Verifica che la tabella sia stata creata
        tables = self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t[0] for t in tables]
        self.assertIn("documents", table_names, "La tabella 'documents' non è stata creata")
    
    def test_migrate_from_json(self):
        """Testa la migrazione da JSON."""
        # Ricrea il database con migrazione
        self.db.close()
        self.db = DocumentDatabase(data_dir=self.test_dir, migrate_from_json=True)
        
        # Verifica che i documenti siano stati migrati
        docs = self.db.get_all_documents()
        self.assertEqual(len(docs), 2, "I documenti non sono stati migrati correttamente")
        
        # Verifica i dati dei documenti
        doc1 = self.db.get_document("doc1")
        self.assertEqual(doc1["filename"], "test1.pdf", "I dati del documento non sono corretti")
        self.assertEqual(doc1["metadata"]["author"], "Test Author", "I metadati non sono stati migrati correttamente")
    
    def test_crud_operations(self):
        """Testa le operazioni CRUD sul database."""
        # Aggiungi un nuovo documento
        new_doc = {
            "id": "doc3",
            "filename": "test3.pdf",
            "title": "Test Document 3",
            "path": "/path/to/test3.pdf",
            "created_at": "2023-01-03T12:00:00",
            "updated_at": "2023-01-03T12:00:00",
            "metadata": {"pages": 15, "author": "Third Author"}
        }
        
        # Inserisci il documento
        self.db.insert_document(new_doc)
        
        # Verifica che il documento sia stato inserito
        doc3 = self.db.get_document("doc3")
        self.assertIsNotNone(doc3, "Il documento non è stato inserito")
        self.assertEqual(doc3["title"], "Test Document 3", "I dati del documento non sono corretti")
        
        # Aggiorna il documento
        doc3["title"] = "Updated Test Document 3"
        doc3["metadata"]["pages"] = 20
        self.db.update_document(doc3)
        
        # Verifica l'aggiornamento
        updated_doc = self.db.get_document("doc3")
        self.assertEqual(updated_doc["title"], "Updated Test Document 3", "Il documento non è stato aggiornato")
        self.assertEqual(updated_doc["metadata"]["pages"], 20, "I metadati non sono stati aggiornati")
        
        # Elimina il documento
        self.db.delete_document("doc3")
        
        # Verifica l'eliminazione
        deleted_doc = self.db.get_document("doc3")
        self.assertIsNone(deleted_doc, "Il documento non è stato eliminato")
    
    def test_get_all_documents(self):
        """Testa il recupero di tutti i documenti."""
        # Migra i documenti di test
        self.db.close()
        self.db = DocumentDatabase(data_dir=self.test_dir, migrate_from_json=True)
        
        # Recupera tutti i documenti
        docs = self.db.get_all_documents()
        
        # Verifica il risultato
        self.assertEqual(len(docs), 2, "Il numero di documenti non corrisponde")
        self.assertIsInstance(docs, dict, "Il risultato non è un dizionario")
        self.assertIn("doc1", docs, "Il documento 'doc1' non è presente")
        self.assertIn("doc2", docs, "Il documento 'doc2' non è presente")
    
    def test_export_to_json(self):
        """Testa l'esportazione in JSON."""
        # Migra i documenti di test
        self.db.close()
        self.db = DocumentDatabase(data_dir=self.test_dir, migrate_from_json=True)
        
        # Esporta in JSON
        export_path = os.path.join(self.test_dir, "export.json")
        result = self.db.export_to_json(export_path)
        
        # Verifica il risultato
        self.assertTrue(result, "L'esportazione è fallita")
        self.assertTrue(os.path.exists(export_path), "Il file di esportazione non è stato creato")
        
        # Verifica il contenuto del file
        with open(export_path, 'r') as f:
            exported_docs = json.load(f)
        
        self.assertEqual(len(exported_docs), 2, "Il numero di documenti esportati non corrisponde")
        self.assertIn("doc1", exported_docs, "Il documento 'doc1' non è stato esportato")
        self.assertIn("doc2", exported_docs, "Il documento 'doc2' non è stato esportato")

class TestMetadataStoreManager(unittest.TestCase):
    """Test per la classe MetadataStoreManager."""
    
    def setUp(self):
        """Configura l'ambiente di test."""
        # Crea una directory temporanea per i test
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"Directory test creata: {self.test_dir}")
        
        # Crea le sottodirectory necessarie
        os.makedirs(os.path.join(self.test_dir, "data"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "files"), exist_ok=True)
        
        # Crea un file JSON di test
        self.test_docs = {
            "doc1": {
                "id": "doc1",
                "filename": "test1.pdf",
                "title": "Test Document 1",
                "path": "/path/to/test1.pdf",
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
                "metadata": {"pages": 5, "author": "Test Author"}
            },
            "doc2": {
                "id": "doc2",
                "filename": "test2.pdf",
                "title": "Test Document 2",
                "path": "/path/to/test2.pdf",
                "created_at": "2023-01-02T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "metadata": {"pages": 10, "author": "Another Author"}
            }
        }
        
        # Scrivi il JSON di test
        json_path = os.path.join(self.test_dir, "data", "documents.json")
        with open(json_path, 'w') as f:
            json.dump(self.test_docs, f)
        
        logger.info(f"File JSON di test creato: {json_path}")
        
        # Inizializza il manager
        self.manager = DocumentManager(
            data_dir=os.path.join(self.test_dir, "data"),
            files_dir=os.path.join(self.test_dir, "files")
        )
    
    def tearDown(self):
        """Pulisce dopo i test."""
        # Chiudi il manager (che chiuderà anche il database)
        if hasattr(self, 'manager') and self.manager:
            if hasattr(self.manager, 'db') and self.manager.db:
                self.manager.db.close()
        
        # Rimuovi la directory temporanea
        shutil.rmtree(self.test_dir)
        logger.info(f"Directory test rimossa: {self.test_dir}")
    
    def test_init_manager(self):
        """Testa l'inizializzazione del manager."""
        # Verifica che il manager sia stato inizializzato
        self.assertIsNotNone(self.manager.db, "Il database non è stato inizializzato")
        
        # Verifica che il database sia stato creato
        db_path = os.path.join(self.test_dir, "data", "documents.db")
        self.assertTrue(os.path.exists(db_path), "Il file del database non è stato creato")
    
    def test_get_documents(self):
        """Testa il recupero dei documenti."""
        # Migra i documenti di test (se necessario)
        if not hasattr(self.manager, 'documents') or not self.manager.documents:
            self.manager.load_documents()
        
        # Verifica che i documenti siano stati caricati
        self.assertEqual(len(self.manager.documents), 2, "I documenti non sono stati caricati correttamente")
        
        # Testa il recupero di un documento
        doc = self.manager.get_document("doc1")
        self.assertIsNotNone(doc, "Il documento non è stato trovato")
        self.assertEqual(doc["filename"], "test1.pdf", "I dati del documento non sono corretti")
        
        # Testa il recupero di tutti i documenti
        all_docs = self.manager.get_all_documents()
        self.assertEqual(len(all_docs), 2, "Non tutti i documenti sono stati recuperati")
    
    def test_add_update_delete_document(self):
        """Testa l'aggiunta, l'aggiornamento e l'eliminazione di documenti."""
        # Crea un nuovo documento
        new_doc = {
            "id": "doc3",
            "filename": "test3.pdf",
            "title": "Test Document 3",
            "path": os.path.join(self.test_dir, "files", "test3.pdf"),
            "metadata": {"pages": 15, "author": "Third Author"}
        }
        
        # Aggiungi il documento
        result = self.manager.add_document(new_doc)
        self.assertTrue(result, "L'aggiunta del documento è fallita")
        
        # Verifica che il documento sia stato aggiunto
        doc3 = self.manager.get_document("doc3")
        self.assertIsNotNone(doc3, "Il documento non è stato aggiunto")
        self.assertEqual(doc3["title"], "Test Document 3", "I dati del documento non sono corretti")
        
        # Aggiorna il documento
        doc3["title"] = "Updated Test Document 3"
        result = self.manager.update_document(doc3)
        self.assertTrue(result, "L'aggiornamento del documento è fallito")
        
        # Verifica l'aggiornamento
        updated_doc = self.manager.get_document("doc3")
        self.assertEqual(updated_doc["title"], "Updated Test Document 3", "Il documento non è stato aggiornato")
        
        # Elimina il documento
        result = self.manager.delete_document("doc3")
        self.assertTrue(result, "L'eliminazione del documento è fallita")
        
        # Verifica l'eliminazione
        deleted_doc = self.manager.get_document("doc3")
        self.assertIsNone(deleted_doc, "Il documento non è stato eliminato")

def run_tests():
    """Esegue i test."""
    # Crea una suite di test
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Aggiungi i test alla suite
    suite.addTest(loader.loadTestsFromTestCase(TestDocumentDatabase))
    suite.addTest(loader.loadTestsFromTestCase(TestMetadataStoreManager))
    
    # Esegui i test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Restituisci un codice di errore se ci sono fallimenti
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
