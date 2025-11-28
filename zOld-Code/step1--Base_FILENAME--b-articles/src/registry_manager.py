"""
Central registry manager for legal case metadata.
Maintains both JSON and CSV formats for all processed files.
"""

import json
import csv
from pathlib import Path
from datetime import datetime


class RegistryManager:
    """Manage central registry of case metadata in JSON and CSV formats."""

    def __init__(self, registry_path_prefix):
        """
        Initialize registry manager.

        Args:
            registry_path_prefix: Path prefix for registry files (e.g., './metadata_registry')
                                 Will create registry_path_prefix.json and .csv
        """
        self.prefix = Path(registry_path_prefix)
        self.json_path = self.prefix.with_suffix('.json')
        self.csv_path = self.prefix.with_suffix('.csv')

    def load_registry(self):
        """
        Load existing registry or create new one.

        Returns:
            dict: Registry structure with metadata and files
        """
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                # If corrupted, create new
                pass

        # Create new registry
        return {
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_files': 0,
                'version': '1.0'
            },
            'files': {}
        }

    def add_or_update_entry(self, registry, file_metadata):
        """
        Add or update a file's metadata in the registry.

        Args:
            registry: Registry dict
            file_metadata: Metadata dict for a single file

        Returns:
            dict: Updated registry
        """
        source_file = file_metadata.get('source_file', 'unknown')

        # Add processing timestamp
        file_metadata['processed_timestamp'] = datetime.now().isoformat()

        # Update or add entry
        registry['files'][source_file] = file_metadata

        # Update registry metadata
        registry['metadata']['last_updated'] = datetime.now().isoformat()
        registry['metadata']['total_files'] = len(registry['files'])

        return registry

    def save_registry_json(self, registry):
        """
        Save registry as JSON file with atomic write.

        Args:
            registry: Registry dict

        Returns:
            Path: Path to saved JSON file
        """
        try:
            # Ensure directory exists
            self.json_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            if self.json_path.exists():
                backup_path = self.json_path.with_suffix('.json.backup')
                try:
                    import shutil
                    shutil.copy2(self.json_path, backup_path)
                except Exception:
                    pass  # Backup failed, but continue

            # Atomic write: write to temp file, then rename
            temp_path = self.json_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)

            # Atomic rename (overwrites existing file)
            temp_path.replace(self.json_path)

            return self.json_path
        except Exception as e:
            print(f"Error saving registry JSON: {e}")
            # Clean up temp file if it exists
            temp_path = self.json_path.with_suffix('.json.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return None

    def save_registry_csv(self, registry):
        """
        Save registry as CSV file with flattened structure.

        Args:
            registry: Registry dict

        Returns:
            Path: Path to saved CSV file
        """
        try:
            # Ensure directory exists
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            files = registry.get('files', {})
            if not files:
                return None

            # Define CSV columns
            columns = [
                'source_file',
                'case_name',
                'court',
                'year',
                'citation',
                'date_decided',
                'date_decided_confidence',
                'docket_number',
                'docket_number_confidence',
                'disposition',
                'disposition_confidence',
                'opinion_author',
                'opinion_author_confidence',
                'opinion_type',
                'opinion_type_confidence',
                'lower_court_judge',
                'lower_court_judge_confidence',
                'panel_members',  # Will be JSON string
                'panel_members_confidence',
                'concurring_judges',  # Flattened
                'dissenting_judges',  # Flattened
                'concurring_dissenting_confidence',
                'attorneys_petitioner',  # Flattened
                'attorneys_respondent',  # Flattened
                'attorneys_appellant',  # Flattened
                'attorneys_appellee',  # Flattened
                'attorneys_confidence',
                'extraction_confidence',
                'extraction_timestamp',
                'processed_timestamp',
            ]

            # Create backup if file exists
            if self.csv_path.exists():
                backup_path = self.csv_path.with_suffix('.csv.backup')
                try:
                    import shutil
                    shutil.copy2(self.csv_path, backup_path)
                except Exception:
                    pass  # Backup failed, but continue

            # Atomic write: write to temp file, then rename
            temp_path = self.csv_path.with_suffix('.csv.tmp')
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()

                for file_metadata in files.values():
                    # Flatten the metadata for CSV
                    flat_row = self._flatten_metadata(file_metadata)
                    writer.writerow(flat_row)

            # Atomic rename (overwrites existing file)
            temp_path.replace(self.csv_path)

            return self.csv_path
        except Exception as e:
            print(f"Error saving registry CSV: {e}")
            # Clean up temp file if it exists
            temp_path = self.csv_path.with_suffix('.csv.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return None

    def _flatten_metadata(self, metadata):
        """
        Flatten nested metadata structure for CSV export.

        Args:
            metadata: Metadata dict

        Returns:
            dict: Flattened metadata suitable for CSV row
        """
        flat = {
            'source_file': metadata.get('source_file', ''),
            'case_name': metadata.get('case_name', ''),
            'court': metadata.get('court', ''),
            'year': metadata.get('year', ''),
            'citation': metadata.get('citation', ''),
            'date_decided': metadata.get('date_decided', ''),
            'date_decided_confidence': metadata.get('date_decided_confidence', ''),
            'docket_number': metadata.get('docket_number', ''),
            'docket_number_confidence': metadata.get('docket_number_confidence', ''),
            'disposition': metadata.get('disposition', ''),
            'disposition_confidence': metadata.get('disposition_confidence', ''),
            'opinion_author': metadata.get('opinion_author', ''),
            'opinion_author_confidence': metadata.get('opinion_author_confidence', ''),
            'opinion_type': metadata.get('opinion_type', ''),
            'opinion_type_confidence': metadata.get('opinion_type_confidence', ''),
            'lower_court_judge': metadata.get('lower_court_judge', ''),
            'lower_court_judge_confidence': metadata.get('lower_court_judge_confidence', ''),
            'extraction_confidence': metadata.get('extraction_confidence', ''),
            'extraction_timestamp': metadata.get('extraction_timestamp', ''),
            'processed_timestamp': metadata.get('processed_timestamp', ''),
        }

        # Panel members - JSON string or comma-separated
        panel = metadata.get('panel_members', [])
        if panel:
            flat['panel_members'] = ', '.join(panel)
            flat['panel_members_confidence'] = metadata.get('panel_members_confidence', '')
        else:
            flat['panel_members'] = ''
            flat['panel_members_confidence'] = ''

        # Concurring/dissenting - extract lists
        concur_dissent = metadata.get('concurring_dissenting', {})
        if concur_dissent:
            flat['concurring_judges'] = ', '.join(concur_dissent.get('concurring', []))
            flat['dissenting_judges'] = ', '.join(concur_dissent.get('dissenting', []))
            flat['concurring_dissenting_confidence'] = metadata.get('concurring_dissenting_confidence', '')
        else:
            flat['concurring_judges'] = ''
            flat['dissenting_judges'] = ''
            flat['concurring_dissenting_confidence'] = ''

        # Attorneys - extract by party
        attorneys = metadata.get('attorneys', {})
        if attorneys:
            flat['attorneys_petitioner'] = ', '.join(attorneys.get('petitioner', []))
            flat['attorneys_respondent'] = ', '.join(attorneys.get('respondent', []))
            flat['attorneys_appellant'] = ', '.join(attorneys.get('appellant', []))
            flat['attorneys_appellee'] = ', '.join(attorneys.get('appellee', []))
            flat['attorneys_confidence'] = metadata.get('attorneys_confidence', '')
        else:
            flat['attorneys_petitioner'] = ''
            flat['attorneys_respondent'] = ''
            flat['attorneys_appellant'] = ''
            flat['attorneys_appellee'] = ''
            flat['attorneys_confidence'] = ''

        return flat

    def update_registry(self, file_metadata):
        """
        Convenience method: load, update, and save registry.

        Args:
            file_metadata: Metadata dict for a file

        Returns:
            tuple: (json_path, csv_path) or (None, None) if failed
        """
        try:
            # Load existing or create new
            registry = self.load_registry()

            # Add or update entry
            registry = self.add_or_update_entry(registry, file_metadata)

            # Save both formats
            json_path = self.save_registry_json(registry)
            csv_path = self.save_registry_csv(registry)

            return (json_path, csv_path)
        except Exception as e:
            print(f"Error updating registry: {e}")
            return (None, None)
