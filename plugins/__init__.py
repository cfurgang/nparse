
import os
import importlib
import inspect
from helpers import config


class Plugin:
    def on_load(self, app):
        pass

    def on_unload(self, app):
        pass

    def on_menu_display(self, menu):
        pass

    def on_menu_click(self, action):
        pass

    def on_app_start(self, app):
        pass

    def on_app_quit(self, app):
        pass


class MetaPlugin:
    def __init__(self, path, manager, module=None):
        self.path = path
        self.manager = manager
        self.module = module
        self.enabled = False
        self.instances = set()

    def __hash__(self):
        return self.path.__hash__()

    def name(self):
        return os.path.basename(self.path)[:os.path.basename(self.path).rfind('.')]

    def is_loaded(self):
        return self.module is not None

    def is_enabled(self):
        return self.enabled

    def is_ready(self):
        return self.is_loaded() and self.is_enabled()

    def load(self):
        module_name = os.path.basename(os.path.dirname(self.path)) + "." + self.name()
        spec = importlib.util.spec_from_file_location(module_name, self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.module = module
        self.enabled = True
        self.instances = set()

        for _, class_ in inspect.getmembers(module):
            if not inspect.isclass(class_):
                continue
            if not issubclass(class_, Plugin):
                continue
            instance = class_()
            self.hook(Plugin.on_load, set([instance]), self.manager.app)
            self.instances.add(instance)

    def unload(self):
        self.enabled = False
        self.hook(Plugin.on_unload, self.instances, self.manager.app)
        self.instances = set()

    def hook(self, hook_name, instances, *kargs, **kwargs):
        # import gdb; gdb.set_trace()
        if instances is None:
            instances = self.instances

        if not isinstance(hook_name, str):
            self.hook(hook_name.__name__, instances, *kargs, **kwargs)
            return

        for instance in instances:
            hook = getattr(instance, hook_name)
            if hook is None:
                continue
            if self.manager.is_in_safe_mode():
                try:
                    hook(*kargs, **kwargs)
                except Exception as e:
                    print("[Plugin] Plugin \"%s\" unloaded because the hook \"%s\" threw an unhandled exception: %s" % (self.name(), hook_name, str(e)))
                    if self.is_enabled():
                        self.unload()
            else:
                hook(*kargs, **kwargs)


class PluginManager:

    def __init__(self, app, directory=os.path.abspath('.')):
        self.app = app
        self.directory = directory
        self.plugins = set()

    def is_in_safe_mode(self):
        #return False
        return config.data['general']['safe_mode']

    def has_plugins(self):
        return len(self.plugins) > 0

    def discover_plugins(self, enable_all):
        plugins = set()
        plugins_dir = os.path.join(self.directory, 'plugins')
        if not os.path.exists(plugins_dir):
            return set()
        for file in os.listdir(plugins_dir):
            if file[:2] == '__' or file[-3:] != '.py':
                continue
            plugin = MetaPlugin(os.path.join(plugins_dir, file), self)
            plugins.add(plugin)
        self.plugins.update(plugins)
        if enable_all:
            for plugin in plugins:
                plugin.load()

    def hook(self, hook_name, *kargs, **kwargs):
        for plugin in self.plugins:
            if not plugin.is_ready():
                continue
            plugin.hook(hook_name, plugin.instances, *kargs, **kwargs)

    def prepare_plugin_menu(self, menu):
        if not self.has_plugins():
            return

        plugins_menu = menu.addMenu('Plugins')
        plugins_options = {}

        for plugin in self.plugins:
            action = plugins_menu.addAction(plugin.name().capitalize())
            action.setCheckable(True)
            action.setChecked(plugin.is_enabled())
            plugins_options[action] = plugin

        def on_click(action):
            plugin = plugins_options.get(action)
            if plugin is None:
                return
            if plugin.is_enabled():
                plugin.unload()
            else:
                plugin.load()

        return on_click




