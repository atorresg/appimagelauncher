import os
import logging
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from locale import setlocale, LC_NUMERIC
from gi.repository import Notify
from itertools import islice
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

logger = logging.getLogger(__name__)
ext_icon = 'images/icon.png'
directories = []
app_images = []


class AppImageLauncherExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesEventListener())
        setlocale(LC_NUMERIC, '')  # set to OS default locale;

    def show_notification(self, title, text=None, icon=ext_icon):
        logger.debug('Show notification: %s' % text)
        icon_full_path = os.path.join(os.path.dirname(__file__), icon)
        Notify.init("AppImageLauncher")
        Notify.Notification.new(title, text, icon_full_path).show()


class KeywordQueryEventListener(EventListener):

    global directories, app_images

    def on_event(self, event, extension):
        return RenderResultListAction(list(islice(self.generate_results(event, extension), 10)))
    
    def generate_results(self, event, extension):
        app_images = [];
        for directory in directories:
            if os.path.isdir(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.AppImage'):
                            app_images.append(os.path.join(root, file))
        if (len(app_images) == 0):
            extension.show_notification("Error", "No AppImages found in the configured directories", icon=ext_icon)
        if event.get_argument():
            app_images = self.filter_strings(app_images, event.get_argument())
        for app_image in app_images:
            yield ExtensionResultItem(
                icon='images/icon.png',
                name=os.path.splitext(os.path.basename(app_image))[0],
                description='Launch {}'.format(os.path.basename(app_image)),
                on_enter=ExtensionCustomAction(app_image)
            )

    def filter_strings(event,strings, filter_text):
        filtered_strings = []
        for string in strings:
            if filter_text.lower() in string.lower():
                filtered_strings.append(string)
        
        return filtered_strings


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        os.system(data)


class PreferencesEventListener(EventListener):

    def on_event(self, event, extension):
        global directories
        string = ''
        if hasattr(event, 'preferences'):
            string = event.preferences['ailauncher_directories']
        else:
            if (event.id=='ailauncher_directories'):
                string = event.new_value
        if string!='':
            directories = []
            list = string.split(',')
            if len(list) == 0:
                extension.show_notification("Error", "No directories found in configuration", icon=ext_icon)
            else:
                home_dir = os.path.expanduser("~")
                for path in list:
                    path = path.strip()
                    if path.startswith("~"):
                        path = path.replace("~", home_dir, 1)
                    if os.path.isdir(path):
                        directories.append(path)

if __name__ == '__main__':
    AppImageLauncherExtension().run()
