"""Módulo datos_prueba.

Contiene la implementación de datos_prueba.py del Sistema de Biblioteca.
"""

from django.core.management.base import BaseCommand

from biblioteca_app.models import (
    Lector,
    Libro,
    Autor,
    Editorial,
    Prestamo,
    LibroAutor,
    LibroEditorial,
)


class Command(BaseCommand):
    """Representa la clase command y encapsula la lógica relacionada con este componente."""
    help = 'Inserta datos de prueba en el sistema de biblioteca'

    def handle(self, *args, **options):

        """Ejecuta la lógica principal del comando de administración."""
        self.stdout.write(
            self.style.WARNING('Insertando datos de prueba...')
        )

        # ========================================================
        # LECTORES
        # ========================================================

        lector1, _ = Lector.objects.get_or_create(
            ApellidoP='González',
            ApellidoM='Pérez',
            Nombres='Juan'
        )

        lector2, _ = Lector.objects.get_or_create(
            ApellidoP='Soto',
            ApellidoM='Muñoz',
            Nombres='María'
        )

        lector3, _ = Lector.objects.get_or_create(
            ApellidoP='Contreras',
            ApellidoM='Rojas',
            Nombres='Pedro'
        )

        # ========================================================
        # AUTORES
        # ========================================================

        autor1, _ = Autor.objects.get_or_create(
            NombreAutor='Gabriel García Márquez'
        )

        autor2, _ = Autor.objects.get_or_create(
            NombreAutor='Isabel Allende'
        )

        autor3, _ = Autor.objects.get_or_create(
            NombreAutor='Antoine de Saint-Exupéry'
        )

        autor4, _ = Autor.objects.get_or_create(
            NombreAutor='Jorge Luis Borges'
        )

        # ========================================================
        # EDITORIALES
        # ========================================================

        editorial1, _ = Editorial.objects.get_or_create(
            NombreEditorial='Editorial Planeta'
        )

        editorial2, _ = Editorial.objects.get_or_create(
            NombreEditorial='Penguin Random House'
        )

        editorial3, _ = Editorial.objects.get_or_create(
            NombreEditorial='Editorial Sudamericana'
        )

        # ========================================================
        # LIBROS
        # ========================================================

        libro1, _ = Libro.objects.get_or_create(
            Titulo='Cien años de soledad'
        )

        libro2, _ = Libro.objects.get_or_create(
            Titulo='La casa de los espíritus'
        )

        libro3, _ = Libro.objects.get_or_create(
            Titulo='El Principito'
        )

        libro4, _ = Libro.objects.get_or_create(
            Titulo='Ficciones'
        )

        libro5, _ = Libro.objects.get_or_create(
            Titulo='Don Quijote de la Mancha'
        )

        # ========================================================
        # LIBRO - AUTOR
        # ========================================================

        relaciones_autor = [
            (libro1, autor1),
            (libro2, autor2),
            (libro3, autor3),
            (libro4, autor4),
        ]

        for libro, autor in relaciones_autor:
            LibroAutor.objects.get_or_create(
                CodLibro=libro,
                CodAutor=autor
            )

        # ========================================================
        # LIBRO - EDITORIAL
        # ========================================================

        relaciones_editorial = [
            (libro1, editorial1),
            (libro2, editorial2),
            (libro3, editorial1),
            (libro4, editorial3),
            (libro5, editorial2),
        ]

        for libro, editorial in relaciones_editorial:
            LibroEditorial.objects.get_or_create(
                CodLibro=libro,
                CodEditorial=editorial
            )

        # ========================================================
        # PRÉSTAMOS
        # ========================================================

        Prestamo.objects.get_or_create(
            CodLibro=libro1,
            CodLector=lector1,
            defaults={
                'FechaDev': '2026-09-10'
            }
        )

        Prestamo.objects.get_or_create(
            CodLibro=libro2,
            CodLector=lector2,
            defaults={
                'FechaDev': '2026-09-15'
            }
        )

        Prestamo.objects.get_or_create(
            CodLibro=libro3,
            CodLector=lector3,
            defaults={
                'FechaDev': '2026-09-20'
            }
        )

        # ========================================================
        # FINAL
        # ========================================================

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                '¡Datos de prueba insertados correctamente!'
            )
        )

        self.stdout.write('')
        self.stdout.write('Datos creados:')
        self.stdout.write('  - 3 lectores')
        self.stdout.write('  - 5 libros')
        self.stdout.write('  - 4 autores')
        self.stdout.write('  - 3 editoriales')
        self.stdout.write('  - 4 relaciones libro-autor')
        self.stdout.write('  - 5 relaciones libro-editorial')
        self.stdout.write('  - 3 préstamos')