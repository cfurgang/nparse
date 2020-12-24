
import os
import importlib
import inspect
from helpers import config


class Plugin:
    def on_load(self, app):
        pass

    def on_unload(self, app):
        pass

    def on_parser_load(self, parser):
        pass

    def on_parser_unload(self, parser):
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
        basename = os.path.basename(self.path)[:os.path.basename(self.path).rfind('.')]
        if "__init__" in basename:
            return os.path.basename(os.path.dirname(self.path))
        return basename

    def package_name(self):
        if "__init__" in os.path.basename(self.path):
            return os.path.basename(os.path.dirname(os.path.dirname(self.path)))
        return os.path.basename(os.path.dirname(self.path))

    def is_loaded(self):
        return self.module is not None

    def is_enabled(self):
        return self.enabled

    def is_ready(self):
        return self.is_loaded() and self.is_enabled()

    def load(self):
        module_name = self.package_name() + "." + self.name()
        spec = importlib.util.spec_from_file_location(module_name, self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.module = module
        self.enabled = True
        self.instances = set()
        found_instances = False

        for _, class_ in inspect.getmembers(module):
            if not inspect.isclass(class_):
                continue
            if not issubclass(class_, Plugin):
                continue
            found_instances = True
            instance = class_()
            self.hook(Plugin.on_load, set([instance]), self.manager.app)
            if self.manager.app and hasattr(self.manager.app, '_parsers'):
                for parser in self.manager.app._parsers:
                    self.hook(Plugin.on_parser_load, set([instance]), parser)
            self.instances.add(instance)

        if not found_instances:
            print("[Plugin] WARNING: The plugin \"%s\" was detected, but no instances of the plugin were found. If this is a package, make sure your Plugin subclass is imported in __init__.py." % self.name())
            self.unload()


    def unload(self):
        self.enabled = False
        if self.manager.app and hasattr(self.manager.app, '_parsers'):
            for parser in self.manager.app._parsers:
                self.hook(Plugin.on_parser_unload, self.instances, parser)
        self.hook(Plugin.on_unload, self.instances, self.manager.app)
        self.instances = set()

    def hook(self, hook_name, instances, *kargs, **kwargs):
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
        return config.data['general']['safe_mode']

    def has_plugins(self):
        return len(self.plugins) > 0

    def discover_plugins(self, enable_all):
        plugins = set()
        plugins_dir = os.path.join(self.directory, 'plugins')

        # Check to make sure the plugins directory exists.
        # If not, we have no plugins.
        if not os.path.exists(plugins_dir):
            return set()

        # Go through the plugins directory
        for file in os.listdir(plugins_dir):
            filepath = os.path.join(plugins_dir, file)

            # If we have a subfolder, try to load __init__.py as a plugin file.
            if os.path.isdir(filepath):
                initpy = os.path.join(filepath, '__init__.py')
                if os.path.exists(initpy):
                    filepath = initpy
                else:
                    continue
            # If we have just a file, make sure it's eligible to be a plugin
            elif file[:2] == '__' or file[-3:] != '.py':
                continue

            # Load the plugin!
            plugin = MetaPlugin(filepath, self)
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

    def extend(self, original, extension):
        pass

    def reduce(self, original, extension):
        pass


class ClassExtension:
    @classmethod
    def get(cls, class_):
        if hasattr(class_, '__extension__'):
            return class_.__extension__
        else:
            extension = ClassExtension(class_)
            class_.__extension__ = extension
            return extension

    @classmethod
    def extend(cls, class_, extension):
        cls.get(class_).extend_class(extension)

    @classmethod
    def reduce(cls, class_, extension):
        cls.get(class_).reduce_class(extension)

    def __init__(self, class_):
        self.class_ = class_
        self.impl = {}

    def super(self, method, obj, *kargs, **kwargs):
        implementations = self.impl.get(method.__name__, [])
        if not implementations or method not in implementations:
            if not implementations:
                return getattr(self.class_, method.__name__)(obj, *kargs, **kwargs)
            else:
                return implementations[-1](obj, *kargs, **kwargs)
        index = implementations.index(method)
        if index == 0:
            raise Exception("You are calling the most original implementation of %s" % str(method.__name__))
        return implementations[index - 1](obj, *kargs, **kwargs)

    def extend_class(self, extension):
        for name, member in inspect.getmembers(extension):
            if name[:2] == '__' or name[-2:] == '__' or not inspect.isfunction(member):
                continue
            implementations = self.impl.get(name, [])
            original_member = getattr(self.class_, name, None)
            if original_member and original_member not in implementations:
                implementations.append(original_member)
            if member not in implementations:
                implementations.append(member)
            setattr(self.class_, name, implementations[-1])
            self.impl[name] = implementations
            print("[ClassExtension] %(class_name)s adding %(extension_type)s method: %(method_name)s" % {
                'class_name': self.class_.__name__,
                'extension_type': 'ADDING NEW' if original_member is None else 'EXTENDING',
                'method_name': name,
            })

    def reduce_class(self, extension):
        for name, member in inspect.getmembers(extension):
            if name[:2] == '__' or name[-2:] == '__' or not inspect.isfunction(member):
                continue
            implementations = self.impl.get(name, [])
            if implementations:
                if member in implementations:
                    implementations.remove(member)
                    print("[ClassExtension] %(class_name)s removing extended method: %(extension_name)s.%(method_name)s" % {
                        'class_name': self.class_.__name__,
                        'extension_name': extension.__name__,
                        'method_name': name,
                    })
            if implementations:
                setattr(self.class_, name, implementations[-1])
            else:
                delattr(self.class_, name)
            self.impl[name] = implementations







