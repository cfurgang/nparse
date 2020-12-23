from helpers import config


class Plugin:

    ALL_PLUGINS = set()
    ENABLED_PLUGINS = set()

    @classmethod
    def load_all_plugins(cls):
        import os
        import importlib
        import sys
        plugins = set()
        pluginfiles = os.listdir('plugins')
        for file in pluginfiles:
            if file[:2] == '__' or file[-3:] != '.py':
                continue
            sys.path.append(os.path.abspath('.'))
            plugin = importlib.import_module("plugins." + file[:file.rfind('.')])
            plugins.add(plugin)
        cls.ALL_PLUGINS.update(plugins)
        cls.ENABLED_PLUGINS.update(plugins)
        cls.describe_plugins()
        return plugins

    @classmethod
    def unload_plugin(cls, plugin):
        import inspect
        if isinstance(plugin, type(inspect)):
            cls.ENABLED_PLUGINS.remove(plugin)
            cls.describe_plugins()
        elif isinstance(plugin, str):
            module_name = 'plugins.' + plugin
            cls.ENABLED_PLUGINS = set(filter(lambda p: p.__name__ != module_name, cls.PLUGINS))
            cls.describe_plugins()
        else:
            cls.unload_plugin(inspect.getmodule(plugin))

    @classmethod
    def hook(cls, hook_name, *kargs, **kwargs):
        for plugin in cls.__subclasses__():
            if not cls.is_enabled_plugin_class(plugin):
                continue
            if isinstance(hook_name, str) and hasattr(plugin, hook_name):
                hook = getattr(plugin, hook_name)
                if cls.is_in_safe_mode():
                    try:
                        hook(plugin, *kargs, **kwargs)
                    except Exception as e:
                        print("[Plugin] FATAL ERROR: Plugin \"%s\" threw unhandled exception: %s" % (plugin.__name__, str(e)))
                        cls.unload_plugin(plugin)
                else:
                    hook(plugin, *kargs, **kwargs)
            elif isinstance(hook_name, type(Plugin.on_app_start)):
                cls.hook(hook_name.__name__, *kargs, **kwargs)

    @classmethod
    def is_enabled_plugin_class(cls, class_):
        for module in cls.ENABLED_PLUGINS:
            if class_.__name__ in list(filter(lambda n: n[:2] != '__', dir(module))):
                return True
        return False

    @classmethod
    def describe_plugins(cls):
        if cls.ALL_PLUGINS:
            print("[Plugin] %d of %d plugins enabled: %s" % (len(cls.ENABLED_PLUGINS), len(cls.ALL_PLUGINS), ", ".join(list(map(lambda p: p.__name__.split('.')[-1], cls.ENABLED_PLUGINS)))))
        if len(cls.ENABLED_PLUGINS) < len(cls.ALL_PLUGINS):
            print("[Plugin] %d of %d plugins disabled: %s" % (len(cls.ALL_PLUGINS) - len(cls.ENABLED_PLUGINS), len(cls.ALL_PLUGINS), ", ".join(list(map(lambda p: p.__name__.split('.')[-1], filter(lambda p: p not in cls.ENABLED_PLUGINS, cls.ALL_PLUGINS))))))

    @classmethod
    def is_in_safe_mode(cls):
        return config.data['general']['safe_mode']

    def on_menu_display(self, menu):
        pass

    def on_menu_click(self, action):
        pass

    def on_app_start(self, app):
        pass

    def on_app_quit(self, app):
        pass

