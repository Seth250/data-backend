import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pois.constants import (
    CSV_EXTENSION,
    JSON_EXTENSION,
    SUPPORTED_FILE_EXTENSIONS,
    XML_EXTENSION,
)
from pois.models import PointOfInterest


class Command(BaseCommand):
    help = 'Load Point of Interest (PoI) data from various file sources (e.g. CSV, JSON, XML) to the database.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skipped = 0

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+', type=str, help='Path to file(s) or directories containing PoI data files.')
        parser.add_argument('-b', '--batch-size', type=int, default=1000, help='Maximum number of items to bulk upsert')

    def handle(self, *args, **options):
        self.stdout.write('Loading file contents, please wait...')
        paths = [Path(path) for path in options['paths']]
        batch_size: int = options['batch_size']

        files = self.get_files(paths)
        if not files:
            raise CommandError('No supported files found')

        data = []
        for file in files:
            extension = file.suffix.lower()
            data.extend(self.load_file_content(file, extension))

        for chunk in self.chunks(data, batch_size):
            PointOfInterest.objects.bulk_create(
                chunk,
                update_conflicts=True,
                update_fields=['name', 'category', 'latitude', 'longitude', 'average_rating'],
                unique_fields=['external_id'],
            )

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {len(data)} Point of Interests (skipped {self.skipped})')
        )

    def load_file_content(self, file_path, extension) -> list[PointOfInterest]:
        if extension == JSON_EXTENSION:
            return self.load_json(file_path)

        elif extension == CSV_EXTENSION:
            return self.load_csv(file_path)

        elif extension == XML_EXTENSION:
            return self.load_xml(file_path)

    def load_json(self, file_path: Path):
        with file_path.open('r', encoding='utf-8') as fp:
            file_content = json.load(fp)

        data = []
        for item in file_content:
            external_id = item.get('id')
            name = item.get('name')
            category = item.get('category')
            coordinates = item.get('coordinates', {})
            latitude = coordinates.get('latitude')
            longitude = coordinates.get('longitude')

            ratings = item.get('ratings', [])

            kwargs = {
                'external_id': external_id,
                'name': name,
                'category': category,
                'latitude': latitude,
                'longitude': longitude,
                'ratings': ratings,
                'average_rating': self.get_average_rating(ratings)
            }

            if not self.has_required_data(kwargs):
                self.stderr.write(
                    self.style.WARNING(f'Skipping invalid record, file={file_path}: {item!r}')
                )
                self.skipped += 1
                continue

            data.append(PointOfInterest(**kwargs))

        return data

    def load_csv(self, file_path: Path):
        data = []

        with file_path.open('r', encoding='utf-8') as fp:
            file_content = csv.DictReader(fp)

            for item in file_content:
                external_id = item.get('poi_id')
                name = item.get('poi_name')
                category = item.get('poi_category')
                latitude = item.get('poi_latitude')
                longitude = item.get('poi_longitude')

                ratings = item.get('poi_ratings', [])
                if ratings and ratings.startswith('{') and ratings.endswith('}'):
                    try:
                        ratings = [float(x) for x in ratings[1:-1].split(',')]
                    except ValueError:
                        ratings = []

                kwargs = {
                    'external_id': external_id,
                    'name': name,
                    'category': category,
                    'latitude': latitude,
                    'longitude': longitude,
                    'ratings': ratings,
                    'average_rating': self.get_average_rating(ratings)
                }

                if not self.has_required_data(kwargs):
                    self.stderr.write(
                        self.style.WARNING(f'Skipping invalid record, file={file_path}: {item!r}')
                    )
                    self.skipped += 1
                    continue

                data.append(PointOfInterest(**kwargs))

        return data

    def load_xml(self, file_path: Path):
        data = []

        tree = ET.parse(file_path)
        root = tree.getroot()
        for i, element in enumerate(root.findall('./DATA_RECORD'), start=1):
            external_id = self.get_xml_element_text(element.find('pid'))
            name = self.get_xml_element_text(element.find('pname'))
            category = self.get_xml_element_text(element.find('pcategory'))
            latitude = self.get_xml_element_text(element.find('platitude'))
            longitude = self.get_xml_element_text(element.find('plongitude'))

            ratings = self.get_xml_element_text(element.find('pratings'))
            if not ratings:
                ratings = []
            else:
                try:
                    ratings = [float(x) for x in ratings.split(',')]
                except ValueError:
                    ratings = []

            kwargs = {
                'external_id': external_id,
                'name': name,
                'category': category,
                'latitude': latitude,
                'longitude': longitude,
                'ratings': ratings,
                'average_rating': self.get_average_rating(ratings)
            }

            if not self.has_required_data(kwargs):
                self.stderr.write(
                    self.style.WARNING(f'Skipping invalid record, position={i}; file={file_path}: {element!r}')
                )
                self.skipped += 1
                continue

            data.append(PointOfInterest(**kwargs))

        return data

    @staticmethod
    def get_files(paths: list[Path]) -> list[Path]:
        files = []
        for path in paths:
            # if the path is a directory, recursively get all files that have our supported extensions
            if path.is_dir():
                for extension in SUPPORTED_FILE_EXTENSIONS:
                    files.extend(path.rglob(f'*{extension}'))

            elif path.is_file() and path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS:
                files.append(path)

        return files

    @staticmethod
    def get_xml_element_text(element) -> str | None:
        if element is not None and element.text:
            return element.text.strip()

        return None

    @staticmethod
    def get_average_rating(ratings: list[int | float]):
        if not ratings:
            return 0

        return sum(ratings) / len(ratings)

    @staticmethod
    def chunks(lst: list[PointOfInterest], batch_size: int):
        for i in range(0, len(lst), batch_size):
            yield lst[i : i + batch_size]

    @staticmethod
    def has_required_data(data: dict):
        required_fields = ('external_id', 'name', 'category', 'longitude', 'latitude')
        return all([data[field] for field in required_fields])
