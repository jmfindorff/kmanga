from __future__ import absolute_import

from django.core.management.base import CommandError
from django.test import mock
from django.test import TestCase

from core.models import Manga
from core.models import Source
from scrapyctl.management.commands.scrapy import Command
from scrapyctl.scrapyctl import ScrapyCtl


class CommandTestCase(TestCase):
    fixtures = ['registration.json', 'core.json']

    def setUp(self):
        self.scrapy = ScrapyCtl('ERROR')
        self.command = Command()
        self.command.stdout = mock.MagicMock()
        self.all_spiders = ['batoto', 'mangareader',
                            'submanga', 'mangafox']

    def test_get_spiders(self):
        """Test recovering the list of scrapy spiders."""
        # This asks directly to Scrapy, not the database
        spiders = self.command._get_spiders(self.scrapy, 'all')
        self.assertEqual(spiders, self.all_spiders)
        spiders = self.command._get_spiders(self.scrapy, 'batoto')
        self.assertEqual(spiders, ['batoto'])

        with self.assertRaises(CommandError):
            self.command._get_spiders(self.scrapy, 'missing')

    def test_get_manga(self):
        """Test recovering the manga instance from a spider."""
        with self.assertRaises(CommandError):
            self.command._get_manga(['Source 1', 'Source 2'])

        with self.assertRaises(CommandError):
            self.command._get_manga(['Source 1'])

        with self.assertRaises(CommandError):
            self.command._get_manga(['Source 1'], manga='missing')

        # Duplicate a Manga
        source = Source.objects.get(name='Source 1')
        manga = source.manga_set.get(name='Manga 1')
        manga.id = None
        manga.save()
        with self.assertRaises(CommandError):
            self.command._get_manga(['Source 1'], manga='Manga 1')
        manga.delete()

        manga1 = self.command._get_manga(['Source 1'], manga='Manga 1')
        manga2 = self.command._get_manga(['Source 1'],
                                         url='http://source1.com/manga1')
        self.assertEqual(manga1, manga2)

    def test_get_issues(self):
        """Test recovering issues list from a manga."""
        manga1 = Manga.objects.get(name='Manga 1')
        manga3 = Manga.objects.get(name='Manga 3')

        with self.assertRaises(CommandError):
            self.command._get_issues(manga1, issues='all')

        with self.assertRaises(CommandError):
            self.command._get_issues(manga1, lang='EN')

        with self.assertRaises(CommandError):
            self.command._get_issues(manga1, issues='all', lang='DE')

        self.assertEqual(self.command._get_issues(manga3,
                                                  issues='all').count(), 5)
        self.assertEqual(
            self.command._get_issues(manga1,
                                     issues='all',
                                     lang='ES').count(), 1)
        self.assertEqual(self.command._get_issues(manga1,
                                                  issues='all',
                                                  lang='EN').count(), 5)

        self.assertEqual(self.command._get_issues(manga1,
                                                  issues='1-5',
                                                  lang='EN').count(), 5)

        self.assertEqual(self.command._get_issues(manga1,
                                                  issues='1,2,3-5',
                                                  lang='EN').count(), 5)

        self.assertEqual(self.command._get_issues(manga1,
                                                  issues='2,1,3',
                                                  lang='EN').count(), 3)
        with self.assertRaises(CommandError):
            self.command._get_issues(manga1, issues='5-1', lang='EN')

        url = 'http://source1.com/manga1/issue1'
        self.assertEqual(self.command._get_issues(manga1,
                                                  issues='1',
                                                  lang='EN').count(),
                         self.command._get_issues(manga1,
                                                  url=url,
                                                  lang='EN').count())

    def test_handle_list(self):
        """Test the `list` handle method."""
        with self.assertRaises(CommandError):
            self.command.handle()

        options = {
            'spiders': 'all',
            'loglevel': 'ERROR',
            'dry-run': False,
        }

        with mock.patch.object(Command, 'list_spiders') as list_spiders:
            c = Command()
            c.handle('list', **options)
        list_spiders.assert_called_once_with(self.all_spiders)

    def test_handle_update_genres(self):
        """Test the `update-genres` handle method."""

        options = {
            'spiders': 'all',
            'loglevel': 'ERROR',
            'dry-run': False,
        }
        _scrapyctl = 'scrapyctl.management.commands.scrapy.ScrapyCtl'
        with mock.patch(_scrapyctl) as scrapyctl:
            scrapyctl.return_value = scrapyctl
            scrapyctl.spider_list.return_value = self.all_spiders
            c = Command()
            c.handle('update-genres', **options)
        scrapyctl.update_genres.assert_called_once_with(self.all_spiders,
                                                        False)

    def test_handle_update_catalog(self):
        """Test the `update-catalog` handle method."""

        options = {
            'spiders': 'all',
            'loglevel': 'ERROR',
            'dry-run': False,
        }
        _scrapyctl = 'scrapyctl.management.commands.scrapy.ScrapyCtl'
        with mock.patch(_scrapyctl) as scrapyctl:
            scrapyctl.return_value = scrapyctl
            scrapyctl.spider_list.return_value = self.all_spiders
            c = Command()
            c.handle('update-catalog', **options)
        scrapyctl.update_catalog.assert_called_once_with(self.all_spiders,
                                                         False)

    def test_handle_update_collection(self):
        """Test the `update-collection` handle method."""

        options = {
            'spiders': 'all',
            'loglevel': 'ERROR',
            'dry-run': False,
            'manga': 'Manga 1',
            'url': None,
        }

        _scrapyctl = 'scrapyctl.management.commands.scrapy.ScrapyCtl'
        with mock.patch(_scrapyctl) as scrapyctl:
            scrapyctl.return_value = scrapyctl
            with mock.patch.object(Command,
                                   '_get_spiders',
                                   return_value=['Source 1']):
                c = Command()
                c.handle('update-collection', **options)
        scrapyctl.update_collection.assert_called_once_with(
            ['Source 1'], 'Manga 1', 'http://source1.com/manga1', False)
