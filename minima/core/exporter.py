from __future__ import annotations
import json
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Any
from minima.core.logger import logger

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DB_DIR = Path("Crawl_data")
EXPORT_DB_DIR.mkdir(parents=True, exist_ok=True)

def _timestamp() -> str:
    """Retourne un timestamp compact pour nommer les fichiers d’export."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class Exporter:
    """Gère l'écriture des résultats au format JSON, CSV et SQLite."""

    def __init__(self, output_dir: Path = EXPORT_DIR, output_db_dir : Path = EXPORT_DB_DIR) -> None:
        self.output_dir = output_dir
        self.output_db_dir = output_db_dir

    def save_json(self, data: Iterable[Mapping[str, Any]], filename: str | None = None) -> Path:
        filename = filename or f"results_{_timestamp()}.json"
        path = self.output_dir / filename


        try:
            with open(path, "w", encoding="utf-8") as jf:
                json.dump(list(data), jf, ensure_ascii=False, indent=2)
            logger.info(f"JSON export -> {path}")
        except Exception as e:
            logger.error(f"Export JSON failed: {e}")
            raise
        return path

    def save_csv(self, data: Iterable[Mapping[str, Any]], filename: str | None = None) -> Path:
        filename = filename or f"results_{_timestamp()}.csv"
        path = self.output_dir / filename
        data_list = list(data)

        try:
            if not data_list:
                logger.warning("No results to export in CSV")
                path.touch()
                return path

            with open(path, "w", newline="", encoding="utf-8") as cf:
                writer = csv.DictWriter(cf, fieldnames=data_list[0].keys())
                writer.writeheader()
                writer.writerows(data_list)
            logger.info(f"CSV export -> {path}")
        except Exception as e:
            logger.error(f"Export CSV failed: {e}")
            raise
        return path

    def save_sqlite(self, data: Iterable[Mapping[str, Any]], filename: str | None = None, table_name: str = "results") -> Path:
        """Exporte les résultats en base de données SQLite."""
        filename = filename or f"results_{_timestamp()}.db"
        path = self.output_db_dir / filename
        data_list = list(data)

        try:
            if not data_list:
                logger.warning("No results to export in SQLite")
                # Crée une base vide
                conn = sqlite3.connect(path)
                conn.close()
                return path

            # Connexion à la base SQLite
            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Récupère les clés/colonnes du premier dictionnaire
            columns = data_list[0].keys()

            # Crée la table avec les colonnes appropriées
            create_table_sql = f"CREATE TABLE {table_name} ({', '.join([f'{col} TEXT' for col in columns])})"
            cursor.execute(create_table_sql)

            # Insère les données
            placeholders = ", ".join(["?" for _ in columns])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            for record in data_list:
                values = [str(record.get(col, "")) for col in columns]
                cursor.execute(insert_sql, values)

            conn.commit()
            conn.close()
            logger.info(f"SQLite export -> {path} (table: {table_name}, rows: {len(data_list)})")
        except Exception as e:
            logger.error(f"Export SQLite failed: {e}")
            raise
        return path

    def export_results(self, results: Iterable[Mapping[str, Any]], prefix: str = "results") -> tuple[Path, Path, Path]:
        timestamp = _timestamp()
        json_path = self.save_json(results, f"{prefix}_{timestamp}.json")
        csv_path = self.save_csv(results, f"{prefix}_{timestamp}.csv")
        db_path = self.save_sqlite(results, f"{prefix}_{timestamp}.db", table_name=prefix)
        return json_path, csv_path, db_path


# --- Compatibilité rétroactive avec l'ancien appel ---
def export_results(results: Iterable[Mapping[str, Any]], prefix: str = "results") -> tuple[Path, Path, Path]:
    """
    Fonction de compatibilité : exporte les résultats en JSON, CSV et SQLite.
    Utilise la classe Exporter interne.
    """
    exporter = Exporter()
    return exporter.export_results(results, prefix)
